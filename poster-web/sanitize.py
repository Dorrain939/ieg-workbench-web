"""
sanitize.py — 富文本 HTML 后端安全清洗
======================================

设计原则（2026-06-25 与 PM Dorrain 确认）：
  1. 所见即所得：后端不改用户样式，只删危险
  2. 闸 2 = 安全清洗（防 XSS），不做品牌兜底
  3. 白名单制：tag / attr / style 属性都白名单

只删：
  - <script>, <iframe>, <object>, <embed>, <link>, <meta>, <style>（避免 CSP 旁路）
  - 所有 on* 事件属性（onclick / onerror / onload …）
  - href 中的 javascript: / data:text/html
  - 危险 CSS 属性（position / transform / float / filter / behavior / expression）

保留：
  - 字体 / 字号 / 颜色 / 高亮 / 行高 / 对齐 / 宽高 等用户排版样式
  - 富文本通用结构 tag：p / span / strong / em / u / s / mark / br / ul / ol / li / a / img

集成方式：
  from sanitize import sanitize_rich_html
  module["data"][slot_html_key] = sanitize_rich_html(raw_html)

依赖：
  pip install bleach>=6.1 tinycss2>=1.2
"""
from __future__ import annotations
import re
from typing import Any, Optional

try:
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False


# ----------------------------------------------------------
# 白名单配置
# ----------------------------------------------------------
ALLOWED_TAGS = [
    "p", "span", "strong", "em", "u", "s", "mark", "br",
    "ul", "ol", "li",
    "a", "img",
    # 兼容：以下 tag 不主动产出，但允许接收（来自其它富文本粘贴）
    "div", "blockquote", "figure", "figcaption",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "td", "th",
]

ALLOWED_ATTRIBUTES = {
    "*":   ["style", "class", "data-image-align", "data-mid"],
    "a":   ["href", "target", "rel", "title"],
    "img": ["src", "alt", "width", "height", "title"],
    "td":  ["colspan", "rowspan"],
    "th":  ["colspan", "rowspan"],
}

ALLOWED_CSS_PROPERTIES = [
    # 字体相关
    "color", "background-color",
    "font-family", "font-size", "font-weight", "font-style",
    "text-decoration", "text-decoration-line", "text-decoration-color",
    "text-align", "line-height",
    "letter-spacing", "word-spacing",
    "vertical-align",
    # 尺寸（允许图片自由拖拽尺寸）
    "width", "height", "max-width", "max-height", "min-width", "min-height",
    # margin / padding（轻度排版）
    "margin", "margin-top", "margin-bottom", "margin-left", "margin-right",
    "padding", "padding-top", "padding-bottom", "padding-left", "padding-right",
]

# 这些 CSS 属性即使白名单也强制剔除（防越界 / 视觉混乱）
FORBIDDEN_CSS_PROPS = {
    "position", "top", "bottom", "left", "right", "z-index",
    "float", "clear",
    "transform", "filter", "backdrop-filter",
    "animation", "transition",
    "behavior", "expression",  # 老 IE
    "-webkit-transform", "-moz-transform",
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto", "tel"]

# 允许的 image src 协议 + 域名规则（None 表示不限制域名）
IMAGE_SRC_ALLOWED_PREFIXES: Optional[list[str]] = None  # 例如 ["/uploads/", "/api/"]


# ----------------------------------------------------------
# 主接口
# ----------------------------------------------------------
def sanitize_rich_html(html: Any, allow_image: bool = True) -> str:
    """
    清洗富文本 HTML 片段。

    :param html: 用户提交的 HTML 字符串；非字符串原样返回 ""
    :param allow_image: 是否允许 <img>；False 时所有图片被剥离
    :return: 清洗后的 HTML 字符串

    保留所有用户样式（font-size / color / 等），仅删除危险内容。
    若未安装 bleach，降级为正则去 <script>，并打印警告（生产环境必须装）。
    """
    if not html or not isinstance(html, str):
        return ""

    if not BLEACH_AVAILABLE:
        # 紧急降级：起码删 <script> 和 on* 属性
        import warnings
        warnings.warn(
            "[sanitize_rich_html] bleach 未安装，使用降级清洗（不推荐生产使用）。"
            " 请执行：pip install bleach tinycss2",
            RuntimeWarning,
        )
        return _fallback_strip(html)

    tags = list(ALLOWED_TAGS)
    if not allow_image and "img" in tags:
        tags.remove("img")

    css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)

    cleaned = bleach.clean(
        html,
        tags=tags,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=css_sanitizer,
        strip=True,            # 不在白名单的 tag 删掉（而不是转义）
        strip_comments=True,
    )

    # 二次过滤：剔除 FORBIDDEN_CSS_PROPS（CSSSanitizer 不会管这些）
    cleaned = _strip_forbidden_css(cleaned)

    # 三次过滤：图片 src 白名单
    if allow_image and IMAGE_SRC_ALLOWED_PREFIXES is not None:
        cleaned = _filter_image_src(cleaned, IMAGE_SRC_ALLOWED_PREFIXES)

    return cleaned


def sanitize_module_data(module: dict, slot_html_keys: list[str]) -> dict:
    """
    便捷工具：清洗模块 data 中的多个槽位字段。
    例如：sanitize_module_data(module, ["body_html", "title_html"])
    """
    if not isinstance(module, dict):
        return module
    data = module.get("data") or {}
    for key in slot_html_keys:
        if key in data and isinstance(data[key], str):
            allow_image = key.endswith("_html") and (
                "body" in key or "intro" in key or "bio" in key or "content" in key
            )
            data[key] = sanitize_rich_html(data[key], allow_image=allow_image)
    return module


def sanitize_payload_deep(obj: Any, html_key_suffix: str = "_html") -> Any:
    """
    深度遍历任意嵌套 dict / list，凡是 key 以 html_key_suffix 结尾的字符串
    字段都自动 sanitize。这是接入富文本最简单的方式——
    在 FastAPI 路由顶部一行调用即可：

        payload = sanitize_payload_deep(payload)

    无需关心模块结构，无需逐个声明字段名。

    设计意图：富文本字段统一命名约定 `*_html`（例如 body_html / title_html），
    这个函数会自动找到它们并清洗。

    :param obj: 任意 dict / list / str / 标量
    :param html_key_suffix: 富文本字段的命名后缀，默认 "_html"
    :return: 新对象（原地修改 + 返回，便于链式）
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and isinstance(k, str) and k.endswith(html_key_suffix):
                # 长内容字段（body/intro/bio/content 系列）默认允许图片
                allow_image = any(token in k for token in ("body", "intro", "bio", "content", "desc"))
                obj[k] = sanitize_rich_html(v, allow_image=allow_image)
            elif isinstance(v, (dict, list)):
                sanitize_payload_deep(v, html_key_suffix)
        return obj
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                sanitize_payload_deep(item, html_key_suffix)
        return obj
    return obj


# ----------------------------------------------------------
# 内部工具
# ----------------------------------------------------------
_STYLE_RE = re.compile(r'style="([^"]*)"', re.IGNORECASE)

def _strip_forbidden_css(html: str) -> str:
    """从所有 style="" 属性里剔除 FORBIDDEN_CSS_PROPS。"""
    def cleanup_style(m):
        raw = m.group(1)
        items = []
        for chunk in raw.split(";"):
            chunk = chunk.strip()
            if not chunk or ":" not in chunk:
                continue
            prop, _, val = chunk.partition(":")
            prop = prop.strip().lower()
            if prop in FORBIDDEN_CSS_PROPS:
                continue
            items.append(f"{prop}: {val.strip()}")
        return f'style="{"; ".join(items)}"' if items else ""
    return _STYLE_RE.sub(cleanup_style, html)


_IMG_SRC_RE = re.compile(r'<img\b[^>]*?\bsrc="([^"]*)"', re.IGNORECASE)

def _filter_image_src(html: str, allowed_prefixes: list[str]) -> str:
    """图片 src 必须以白名单前缀开头，否则替换为占位 / 删除。"""
    def check(m):
        src = m.group(1)
        if any(src.startswith(p) for p in allowed_prefixes) or src.startswith("http"):
            return m.group(0)
        # 不在白名单，删 src
        return m.group(0).replace(f'src="{src}"', 'src=""')
    return _IMG_SRC_RE.sub(check, html)


_SCRIPT_RE = re.compile(r'<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>', re.IGNORECASE)
_ON_ATTR_RE = re.compile(r'\s+on\w+\s*=\s*"[^"]*"', re.IGNORECASE)
_JAVASCRIPT_RE = re.compile(r'(href|src)\s*=\s*"\s*javascript:[^"]*"', re.IGNORECASE)

def _fallback_strip(html: str) -> str:
    """bleach 不可用时的最小降级清洗。"""
    html = _SCRIPT_RE.sub("", html)
    html = _ON_ATTR_RE.sub("", html)
    html = _JAVASCRIPT_RE.sub(r'\1=""', html)
    return html


# ----------------------------------------------------------
# 自测：可直接 python sanitize.py 跑
# ----------------------------------------------------------
if __name__ == "__main__":
    samples = [
        # XSS：script
        '<p>正常文字<script>alert("xss")</script></p>',
        # XSS：onclick
        '<p onclick="alert(1)" style="color:red">点我</p>',
        # XSS：javascript: href
        '<a href="javascript:alert(1)">link</a>',
        # 正常用户样式（应完整保留）
        '<p style="font-family:腾讯体;font-size:24px;color:#7B2CBF"><strong>训练营</strong></p>',
        # 危险 CSS：position
        '<p style="position:fixed;top:0;color:red">overlay</p>',
        # 图片 + width/height（应保留）
        '<p><img src="/uploads/a.png" width="200" height="150" /></p>',
        # 段落对齐属性（自定义 data 属性应保留）
        '<p data-image-align="center" style="text-align:center"><img src="/x.png" /></p>',
        # 混合
        '<p>hi<iframe src="evil.com"></iframe><span style="background-color:#FFEB3B">高亮</span></p>',
    ]
    print(f"BLEACH_AVAILABLE = {BLEACH_AVAILABLE}\n")
    for s in samples:
        print("IN :", s)
        print("OUT:", sanitize_rich_html(s))
        print("-" * 60)
