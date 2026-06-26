"""项目工作台 CRUD：projects/<pid>/project.json + artifacts/ 子目录。

不引入数据库，每个项目一个 JSON 文件。
artifact 子目录组织：projects/<pid>/artifacts/<skill>/<YYYYMMDD_HHMMSS>/
"""
from __future__ import annotations

import json
import pathlib
import shutil
import uuid
import time
import datetime
import math
import html
from html.parser import HTMLParser
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from app_paths import WEB_ROOT, PROJECTS_DIR, GENERATED_COVERS_DIR, UPLOADS_DIR

PROJECTS_DIR.mkdir(exist_ok=True)
COVERS_DIR = WEB_ROOT / "static" / "covers"
GENERATED_COVERS_DIR.mkdir(parents=True, exist_ok=True)


# 预制封面清单（id, label, url, 主色调）
COVER_LIBRARY = [
    {"id": "blue_business", "label": "深蓝商务", "url": "/static/covers/cover_blue_business.svg", "tone": "#1E40AF"},
    {"id": "orange_intern", "label": "暖橙实习", "url": "/static/covers/cover_orange_intern.svg", "tone": "#EA580C"},
    {"id": "dark_security", "label": "暗蓝安全", "url": "/static/covers/cover_dark_security.svg", "tone": "#312E81"},
    {"id": "purple_review", "label": "深紫复盘", "url": "/static/covers/cover_purple_review.svg", "tone": "#7C3AED"},
    {"id": "cyan_leadership", "label": "晴蓝领导力", "url": "/static/covers/cover_cyan_leadership.svg", "tone": "#0369A1"},
    {"id": "teal_campus", "label": "青翠校园", "url": "/static/covers/cover_teal_campus.svg", "tone": "#0F766E"},
    {"id": "pink_security", "label": "粉调温暖", "url": "/static/covers/cover_pink_security.svg", "tone": "#BE185D"},
    {"id": "tech_dark", "label": "暗夜科技", "url": "/static/covers/cover_tech_dark.svg", "tone": "#1E293B"},
]
COVER_BY_ID = {c["id"]: c for c in COVER_LIBRARY}


# 项目状态枚举
VALID_STATUS = {"in_progress", "pending", "archived"}


router = APIRouter(prefix="/api")


# ============================================================
# 富文本 HTML 清洗
# ============================================================
RICH_HTML_TAGS = {
    "span", "b", "strong", "i", "em", "u", "br", "p", "div", "img",
}
RICH_HTML_DROP_CONTENT_TAGS = {
    "script", "style", "iframe", "object", "embed", "link", "meta",
}
RICH_HTML_VOID_TAGS = {"br", "img"}
RICH_HTML_ATTRS = {
    "*": {"class", "style", "title", "data-asset-path"},
    "img": {"src", "alt", "title", "class", "style", "width", "height", "data-asset-path"},
    "span": {"class", "style", "title", "contenteditable", "data-asset-path"},
    "div": {"class", "style", "title", "data-asset-path"},
    "p": {"class", "style", "title", "data-asset-path"},
}
RICH_HTML_STYLE_PROPS = {
    "color",
    "background-color",
    "font-size",
    "font-family",
    "font-weight",
    "font-style",
    "text-decoration",
    "text-align",
    "line-height",
    "width",
    "height",
    "max-width",
}


def _safe_rich_url(value: str) -> str:
    raw = (value or "").strip()
    lowered = raw.lower().replace("\x00", "")
    if not raw:
        return ""
    if lowered.startswith(("javascript:", "vbscript:", "file:")):
        return ""
    if lowered.startswith("data:"):
        return raw if lowered.startswith(("data:image/png", "data:image/jpeg", "data:image/jpg", "data:image/gif", "data:image/webp")) else ""
    if raw.startswith(("/api/asset/", "/api/skill-asset?", "/static/")):
        return raw
    return ""


def _safe_rich_style(value: str) -> str:
    safe_parts: list[str] = []
    for item in (value or "").split(";"):
        if ":" not in item:
            continue
        prop, raw_val = item.split(":", 1)
        prop = prop.strip().lower()
        raw_val = raw_val.strip()
        lowered_val = raw_val.lower().replace("\\", "")
        if prop not in RICH_HTML_STYLE_PROPS or not raw_val:
            continue
        if any(token in lowered_val for token in ("javascript:", "expression(", "url(", "@import", "behavior:")):
            continue
        safe_parts.append(f"{prop}: {raw_val}")
    return "; ".join(safe_parts)


def _safe_rich_class(value: str) -> str:
    tokens = []
    for token in (value or "").split():
        clean = "".join(ch for ch in token if ch.isalnum() or ch in {"_", "-"})
        if clean:
            tokens.append(clean[:64])
    return " ".join(tokens[:12])


class _RichHtmlSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        tag = (tag or "").lower()
        if tag in RICH_HTML_DROP_CONTENT_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth or tag not in RICH_HTML_TAGS:
            return
        allowed = set(RICH_HTML_ATTRS.get("*", set())) | set(RICH_HTML_ATTRS.get(tag, set()))
        cleaned = []
        has_safe_src = False
        for name, value in attrs or []:
            name = (name or "").lower()
            value = value or ""
            if name.startswith("on") or name not in allowed:
                continue
            if name in {"src"}:
                value = _safe_rich_url(value)
                if not value:
                    continue
                has_safe_src = True
            elif name == "style":
                value = _safe_rich_style(value)
                if not value:
                    continue
                value = html.escape(value, quote=True)
            elif name == "class":
                value = _safe_rich_class(value)
                if not value:
                    continue
            elif name == "contenteditable":
                value = "false" if str(value).lower() == "false" else ""
                if not value:
                    continue
            else:
                value = html.escape(str(value), quote=True)
            cleaned.append(f'{name}="{value}"')
        if tag == "img" and not has_safe_src:
            return
        attr_text = f" {' '.join(cleaned)}" if cleaned else ""
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str):
        tag = (tag or "").lower()
        if tag in RICH_HTML_DROP_CONTENT_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth or tag not in RICH_HTML_TAGS or tag in RICH_HTML_VOID_TAGS:
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str):
        if not self.skip_depth:
            self.parts.append(html.escape(data or "", quote=False))

    def handle_entityref(self, name: str):
        if not self.skip_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str):
        if not self.skip_depth:
            self.parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self.parts)


def sanitize_rich_html(value) -> str:
    parser = _RichHtmlSanitizer()
    parser.feed(str(value or ""))
    parser.close()
    return parser.get_html()


# TipTap / ProseMirror editor_json 白名单：后端只保留渲染端可消费的安全结构。
EDITOR_JSON_NODE_TYPES = {"doc", "paragraph", "text", "hardBreak", "posterImage", "image", "bulletList", "orderedList", "listItem"}
EDITOR_JSON_MARK_TYPES = {"bold", "italic", "underline", "textStyle", "highlight"}
EDITOR_JSON_NODE_ATTRS = {"textAlign", "src", "path", "alt", "widthPct", "width_pct", "align"}
EDITOR_JSON_MARK_ATTRS = {"color", "fontSize", "fontFamily"}


def _safe_editor_json_url(value: str) -> str:
    return _safe_rich_url(value)


def sanitize_editor_json(value):
    if not isinstance(value, dict):
        return None
    node_type = str(value.get("type") or "")
    if node_type not in EDITOR_JSON_NODE_TYPES:
        return None
    out = {"type": node_type}
    if node_type == "text":
        out["text"] = str(value.get("text") or "")[:20000]
    attrs = value.get("attrs") if isinstance(value.get("attrs"), dict) else {}
    clean_attrs = {}
    for k, v in attrs.items():
        if k not in EDITOR_JSON_NODE_ATTRS:
            continue
        if k in {"src"}:
            sv = _safe_editor_json_url(str(v or ""))
            if sv:
                clean_attrs[k] = sv
        elif k in {"path"}:
            sv = str(v or "").strip()
            if sv.startswith(("projects/", "generated/", "static/", "/static/")) or sv.startswith("/api/"):
                clean_attrs[k] = sv[:1000]
            else:
                try:
                    ap = pathlib.Path(sv).expanduser().resolve()
                    allowed = [UPLOADS_DIR.resolve(), PROJECTS_DIR.resolve(), (WEB_ROOT / "static").resolve(), pathlib.Path.home() / ".codebuddy" / "skills" / "gaming-training-poster" / "assets" / "uploads", pathlib.Path.home() / "Desktop" / "poster-web-backup-20260607-194209" / "poster-web" / "uploads"]
                    for root in allowed:
                        try:
                            ap.relative_to(root.resolve())
                            clean_attrs[k] = str(ap)[:1000]
                            break
                        except Exception:
                            continue
                except Exception:
                    pass
        elif k in {"widthPct", "width_pct"}:
            try:
                clean_attrs[k] = max(0.05, min(1.0, float(v)))
            except Exception:
                pass
        elif k == "align":
            clean_attrs[k] = str(v) if str(v) in {"left", "center", "right"} else "center"
        elif k == "textAlign":
            clean_attrs[k] = str(v) if str(v) in {"left", "center", "right", "justify"} else "left"
        else:
            clean_attrs[k] = html.escape(str(v or "")[:500], quote=True)
    if clean_attrs:
        out["attrs"] = clean_attrs
    marks = value.get("marks") if isinstance(value.get("marks"), list) else []
    clean_marks = []
    for mark in marks[:32]:
        if not isinstance(mark, dict):
            continue
        mt = str(mark.get("type") or "")
        if mt not in EDITOR_JSON_MARK_TYPES:
            continue
        mo = {"type": mt}
        mattrs = mark.get("attrs") if isinstance(mark.get("attrs"), dict) else {}
        clean_mattrs = {}
        for ak, av in mattrs.items():
            if ak not in EDITOR_JSON_MARK_ATTRS:
                continue
            sv = str(av or "").strip()
            if ak == "color":
                if sv == "transparent" or sv.startswith("#") or sv.lower().startswith(("rgb(", "rgba(")):
                    clean_mattrs[ak] = sv[:64]
            elif ak == "fontSize":
                if sv.endswith("px"):
                    try:
                        px = max(8, min(160, float(sv[:-2])))
                        clean_mattrs[ak] = f"{px:g}px"
                    except Exception:
                        pass
            elif ak == "fontFamily":
                clean_mattrs[ak] = html.escape(sv[:160], quote=True)
        if clean_mattrs:
            mo["attrs"] = clean_mattrs
        clean_marks.append(mo)
    if clean_marks:
        out["marks"] = clean_marks
    content = value.get("content") if isinstance(value.get("content"), list) else []
    clean_content = []
    for child in content[:500]:
        c = sanitize_editor_json(child)
        if c is not None:
            clean_content.append(c)
    if clean_content:
        out["content"] = clean_content
    return out


def sanitize_rich_payload(value, key: str = ""):
    """递归清洗所有 *_html 与 *_editor_json/editor_json 字段。"""
    if isinstance(value, dict):
        if key == "editor_json" or key.endswith("_editor_json"):
            return sanitize_editor_json(value) or {"type": "doc", "content": [{"type": "paragraph"}]}
        return {k: sanitize_rich_payload(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_rich_payload(v, key) for v in value]
    if isinstance(value, str) and key.endswith("_html"):
        return sanitize_rich_html(value)
    return value


# ============================================================
# 内部工具
# ============================================================
def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _gen_pid() -> str:
    """生成项目 ID：proj_YYYYMMDD_随机 8 位"""
    today = datetime.date.today().strftime("%Y%m%d")
    return f"proj_{today}_{uuid.uuid4().hex[:8]}"


def _gen_code() -> str:
    """生成对外项目编号：PRJ-YYMMDD"""
    today = datetime.date.today().strftime("%y%m%d")
    return f"PRJ-{today}"


def _gen_function_project_id(function_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (function_id or "func"))
    return f"fp_{safe}_{uuid.uuid4().hex[:8]}"


def _project_dir(pid: str) -> pathlib.Path:
    if not pid.startswith("proj_") or "/" in pid or ".." in pid:
        raise HTTPException(400, f"非法项目 ID: {pid}")
    return PROJECTS_DIR / pid


def _read_project(pid: str) -> dict:
    fp = _project_dir(pid) / "project.json"
    if not fp.exists():
        raise HTTPException(404, f"项目不存在: {pid}")
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_project(pid: str, data: dict) -> None:
    pdir = _project_dir(pid)
    pdir.mkdir(exist_ok=True)
    data["updated_at"] = _now_iso()
    fp = pdir / "project.json"
    tmp = pdir / "project.json.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(fp)


def _function_projects(data: dict, function_id: str) -> list:
    groups = data.setdefault("function_projects", {})
    items = groups.setdefault(function_id, [])
    if not isinstance(items, list):
        groups[function_id] = []
        items = groups[function_id]
    return items


def _safe_cover_id(prefix: str = "cover") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _dynamic_cover_obj(cover_id: str | None) -> Optional[dict]:
    if not cover_id:
        return None
    fp = GENERATED_COVERS_DIR / f"{cover_id}.png"
    if not fp.exists():
        return None
    return {
        "id": cover_id,
        "label": "项目封面",
        "url": f"/api/covers/generated/{cover_id}.png",
        "tone": "#2563EB",
    }


def _cover_obj(cover_id: str | None) -> Optional[dict]:
    if not cover_id:
        return None
    return COVER_BY_ID.get(cover_id) or _dynamic_cover_obj(cover_id)


def _valid_cover_id(cover_id: str | None) -> bool:
    return not cover_id or cover_id in COVER_BY_ID or _dynamic_cover_obj(cover_id) is not None


def _font(size: int, bold: bool = False):
    candidates = [
        str(WEB_ROOT / "static" / "fonts" / "TencentSans-W7.ttf"),
        str(WEB_ROOT / "static" / "fonts" / "TencentSans-W7.otf"),
        str(WEB_ROOT / "fonts" / "TencentSans-W7.ttf"),
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int) -> list[str]:
    chars = list((text or "").strip())
    lines: list[str] = []
    line = ""
    for ch in chars:
        test = line + ch
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = ch
            if len(lines) >= max_lines:
                break
    if line and len(lines) < max_lines:
        lines.append(line)
    if len(lines) == max_lines and len("".join(lines)) < len(chars):
        lines[-1] = lines[-1].rstrip("，。,. ") + "..."
    return lines or ["未命名项目"]


def _render_project_cover(name: str, description: str = "", project_type: str = "", scene: str = "", theme_color: str = "") -> str:
    cover_id = _safe_cover_id("generated")
    width, height = 1175, 500
    fallback = {
        "A": "#2563EB",
        "B": "#0F766E",
        "C": "#7C3AED",
    }.get(str(project_type or "").upper(), "#2563EB")
    primary = theme_color if isinstance(theme_color, str) and theme_color.startswith("#") and len(theme_color) == 7 else fallback
    img = Image.new("RGB", (width, height), "#F8FAFC")
    pix = img.load()

    def hex_rgb(h: str):
        h = h.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    p = hex_rgb(primary)
    brightness = (p[0] * 299 + p[1] * 587 + p[2] * 114) / 1000
    c1 = tuple(min(255, int(v + (255 - v) * 0.10)) for v in p)
    c2 = tuple(min(255, int(v + (255 - v) * 0.72)) for v in p)
    for y in range(height):
        for x in range(width):
            t = (x / width * 0.35) + (y / height * 0.65)
            pix[x, y] = tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3))

    veil_alpha = 18 if brightness < 130 else 6
    veil = Image.new("RGBA", (width, height), (255, 255, 255, veil_alpha))
    img = Image.alpha_composite(img.convert("RGBA"), veil)
    d = ImageDraw.Draw(img)

    title_fill = "#FFFFFF" if brightness < 120 else tuple(max(0, int(v * 0.42)) for v in p)
    shadow_fill = (15, 23, 42, 58) if brightness >= 120 else (0, 0, 0, 92)
    max_w = width - 170
    max_h = height - 120
    title_font = _font(104, True)
    title_lines = [name or "未命名项目"]
    line_step = 120
    for size in range(112, 42, -4):
        font = _font(size, True)
        lines = _wrap_text(d, name or "未命名项目", font, max_w, 2)
        bboxes = [d.textbbox((0, 0), line, font=font) for line in lines]
        line_step = int(size * 1.18)
        total_h = line_step * len(lines) - max(8, int(size * 0.14))
        max_line_w = max((bb[2] - bb[0]) for bb in bboxes) if bboxes else 0
        if max_line_w <= max_w and total_h <= max_h:
            title_font = font
            title_lines = lines
            break

    total_h = line_step * len(title_lines) - max(8, int(line_step * 0.14))
    y = int((height - total_h) / 2)
    for line in title_lines:
        bbox = d.textbbox((0, 0), line, font=title_font)
        x = int((width - (bbox[2] - bbox[0])) / 2)
        d.text((x + 3, y + 5), line, font=title_font, fill=shadow_fill)
        d.text((x, y), line, font=title_font, fill=title_fill)
        y += line_step

    fp = GENERATED_COVERS_DIR / f"{cover_id}.png"
    img.convert("RGB").save(fp, quality=92)
    return cover_id


def _function_project_summary(item: dict) -> dict:
    strategy = item.get("poster_strategy") or {}
    modules = strategy.get("module_plan") or []
    return {
        **item,
        "module_count": len(modules),
        "required_count": sum(1 for m in modules if m.get("required")),
        "optional_count": sum(1 for m in modules if not m.get("required")),
    }


def _summary(data: dict) -> dict:
    """生成列表卡所需的精简字段。"""
    arts = data.get("artifacts") or []

    def _count(skill: str) -> int:
        return sum(1 for a in arts if a.get("skill") == skill)

    cover_id = data.get("cover_id")
    cover_obj = _cover_obj(cover_id)
    return {
        "id": data.get("id"),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "status": data.get("status", "in_progress"),
        "code": data.get("code", ""),
        "owner": data.get("owner") or {"name": "未指派", "initial": "?"},
        "cover_id": cover_id,
        "cover_url": cover_obj["url"] if cover_obj else None,
        "cover_tone": cover_obj["tone"] if cover_obj else "#94A3B8",
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "artifact_count": len(arts),
        "stats": {
            "design_brief": _count("design_brief"),
            "copywriter": _count("copywriter"),
            "poster_render": _count("poster_render"),
        },
    }


def _ensure_seed_projects() -> None:
    """平台正式模式不再自动生成示例项目。"""
    return
    """如果 projects/ 为空，按设计图填 6 个进行中 + 3 个归档项目。"""
    existing = [p for p in PROJECTS_DIR.iterdir() if p.is_dir() and p.name.startswith("proj_")]
    if existing:
        return

    # 按设计图复刻：6 个进行/待启动 + 3 个归档
    seeds = [
        # === 在做的 6 个 ===
        {"name": "2026 新经理训练营海报", "desc": "面向 IEG 新晋管理者的内部培训视觉项目，包含海报、长图、宣发物料等。",
         "status": "in_progress", "owner": {"name": "李想", "initial": "L"}, "cover_id": "blue_business",
         "stats": {"design_brief": 1, "copywriter": 4, "poster_render": 3}},
        {"name": "暑期实习生 onboarding", "desc": "面向暑期实习生的视觉物料",
         "status": "pending", "owner": {"name": "王薇", "initial": "W"}, "cover_id": "orange_intern",
         "stats": {"design_brief": 1, "copywriter": 3, "poster_render": 2}},
        {"name": "游戏安全专项培训", "desc": "提升游戏安全意识专项培训海报项目",
         "status": "in_progress", "owner": {"name": "张子涵", "initial": "Z"}, "cover_id": "dark_security",
         "stats": {"design_brief": 1, "copywriter": 2, "poster_render": 1}},
        {"name": "HRBP 业务复盘会", "desc": "HRBP 团队季度业务复盘会视觉支持项目",
         "status": "in_progress", "owner": {"name": "马克", "initial": "M"}, "cover_id": "purple_review",
         "stats": {"design_brief": 1, "copywriter": 2, "poster_render": 1}},
        {"name": "领导力共创工作坊", "desc": "中高层领导力发展工作坊视觉项目",
         "status": "pending", "owner": {"name": "Shirley", "initial": "S"}, "cover_id": "cyan_leadership",
         "stats": {"design_brief": 0, "copywriter": 0, "poster_render": 0}},
        {"name": "校招生培养计划", "desc": "2026 校招生培养系列培训视觉项目",
         "status": "in_progress", "owner": {"name": "Kelly", "initial": "K"}, "cover_id": "teal_campus",
         "stats": {"design_brief": 1, "copywriter": 2, "poster_render": 1}},
        # === 已归档 3 个 ===
        {"name": "管理者沟通力提升训练营", "desc": "管理者沟通技巧专项培训项目",
         "status": "archived", "owner": {"name": "李想", "initial": "L"}, "cover_id": None,
         "created_offset_days": 60, "stats": {"design_brief": 1, "copywriter": 3, "poster_render": 2}},
        {"name": "数据安全意识月", "desc": "全员数据安全意识提升宣传项目",
         "status": "archived", "owner": {"name": "王薇", "initial": "W"}, "cover_id": None,
         "created_offset_days": 80, "stats": {"design_brief": 1, "copywriter": 2, "poster_render": 1}},
        {"name": "技术分享会系列海报", "desc": "技术团队内部分享会系列海报",
         "status": "archived", "owner": {"name": "张子涵", "initial": "Z"}, "cover_id": None,
         "created_offset_days": 100, "stats": {"design_brief": 1, "copywriter": 4, "poster_render": 2}},
    ]

    for idx, s in enumerate(seeds):
        time.sleep(0.005)  # 保证 pid hex 不重复
        pid = _gen_pid()
        # 模拟 stats 变成 fake artifacts 列表
        artifacts = []
        now = datetime.datetime.now()
        offset_days = s.get("created_offset_days", idx)
        for skill, cnt in (s.get("stats") or {}).items():
            for k in range(cnt):
                ts = now - datetime.timedelta(days=offset_days, hours=k * 3)
                artifacts.append({
                    "id": f"art_{uuid.uuid4().hex[:10]}",
                    "skill": skill,
                    "title": _seed_artifact_title(skill, k + 1),
                    "path": f"artifacts/{skill}/seed_{k}/",
                    "version": f"v{k + 1}.{(k+1) % 3}",
                    "created_at": ts.isoformat(timespec="seconds"),
                })
        artifacts.sort(key=lambda a: a["created_at"], reverse=True)

        created = (now - datetime.timedelta(days=offset_days)).isoformat(timespec="seconds")
        updated = (
            artifacts[0]["created_at"] if artifacts else created
        )
        data = {
            "id": pid,
            "code": _gen_code(),
            "name": s["name"],
            "description": s["desc"],
            "status": s["status"],
            "owner": s["owner"],
            "cover_id": s.get("cover_id"),
            "created_at": created,
            "updated_at": updated,
            "artifacts": artifacts,
        }
        _write_project(pid, data)


def _seed_artifact_title(skill: str, idx: int) -> str:
    """生成 seed artifact 的中文标题。"""
    if skill == "design_brief":
        return f"设计阐释稿 v1.{idx}"
    if skill == "copywriter":
        return ["主标题文案", "副标题文案", "讲师介绍文案", "学员须知文案"][min(idx - 1, 3)]
    if skill == "poster_render":
        return f"海报版本 v{idx}.{idx % 3}"
    return f"产物 #{idx}"


# 启动时确保有种子项目
_ensure_seed_projects()


# ============================================================
# 路由
# ============================================================

@router.get("/covers")
def list_covers():
    """返回预制封面清单。"""
    generated = []
    for fp in sorted(GENERATED_COVERS_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True):
        cid = fp.stem
        generated.append({
            "id": cid,
            "label": "项目封面",
            "url": f"/api/covers/generated/{cid}.png",
            "tone": "#2563EB",
        })
    return {"covers": generated[:24] + COVER_LIBRARY}


@router.get("/covers/generated/{cover_id}.png")
def get_generated_cover(cover_id: str):
    if "/" in cover_id or ".." in cover_id:
        raise HTTPException(400, "非法封面 ID")
    fp = GENERATED_COVERS_DIR / f"{cover_id}.png"
    if not fp.exists():
        raise HTTPException(404, "封面不存在")
    return FileResponse(fp)


@router.post("/covers/generate")
def generate_cover(payload: dict):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "缺少项目名称")
    cover_id = _render_project_cover(
        name=name,
        description=(payload.get("description") or "").strip(),
        project_type=(payload.get("project_type") or "").strip(),
        scene=(payload.get("scene") or "").strip(),
        theme_color=(payload.get("theme_color") or "").strip(),
    )
    return _cover_obj(cover_id)


@router.post("/covers/upload")
async def upload_cover(file: UploadFile = File(...)):
    suffix = pathlib.Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "封面只支持 png/jpg/jpeg/webp")
    cover_id = _safe_cover_id("uploaded")
    raw = GENERATED_COVERS_DIR / f"{cover_id}{suffix}"
    with open(raw, "wb") as f:
        shutil.copyfileobj(file.file, f)
    target = GENERATED_COVERS_DIR / f"{cover_id}.png"
    try:
        im = Image.open(raw).convert("RGB")
        im.thumbnail((1175, 500))
        canvas = Image.new("RGB", (1175, 500), "#F8FAFC")
        x = (1175 - im.width) // 2
        y = (500 - im.height) // 2
        canvas.paste(im, (x, y))
        canvas.save(target, quality=92)
    finally:
        raw.unlink(missing_ok=True)
    return _cover_obj(cover_id)


@router.get("/projects")
def list_projects():
    """返回精简列表。前端再做 tabs 过滤。"""
    items = []
    for pdir in PROJECTS_DIR.iterdir():
        if not pdir.is_dir() or not pdir.name.startswith("proj_"):
            continue
        fp = pdir / "project.json"
        if not fp.exists():
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        items.append(_summary(data))
    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)

    # 顺便算几个统计卡数字
    counts = {"in_progress": 0, "pending": 0, "archived": 0}
    for it in items:
        s = it.get("status") or "in_progress"
        if s in counts:
            counts[s] += 1

    # "本周更新"：updated_at 在最近 7 天内
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    week_updated = sum(1 for it in items if (it.get("updated_at") or "") >= cutoff)

    return {
        "projects": items,
        "stats": {
            "in_progress": counts["in_progress"],
            "pending": counts["pending"],
            "archived": counts["archived"],
            "week_updated": week_updated,
        },
    }


@router.post("/projects")
def create_project(payload: dict):
    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()
    if not name:
        raise HTTPException(400, "缺少 name")

    status = payload.get("status") or "in_progress"
    if status not in VALID_STATUS:
        status = "in_progress"

    owner_in = payload.get("owner") or {}
    owner_name = (owner_in.get("name") or "").strip() or "未指派"
    owner_initial = (owner_in.get("initial") or owner_name[:1] or "?").upper()[:2]

    cover_id = payload.get("cover_id")
    if not _valid_cover_id(cover_id):
        cover_id = None

    pid = _gen_pid()
    data = {
        "id": pid,
        "code": _gen_code(),
        "name": name,
        "description": description,
        "status": status,
        "owner": {"name": owner_name, "initial": owner_initial},
        "cover_id": cover_id,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "artifacts": [],
    }
    if isinstance(payload.get("poster_strategy"), dict):
        data["poster_strategy"] = sanitize_rich_payload(payload["poster_strategy"])
    if payload.get("project_type"):
        data["project_type"] = payload.get("project_type")
    if payload.get("scene"):
        data["scene"] = payload.get("scene")
    _write_project(pid, data)
    return _summary(data)


@router.get("/projects/{pid}")
def get_project(pid: str):
    data = _read_project(pid)
    # 给详情也加上 cover_url 之类便利字段
    summary = _summary(data)
    return {**data, "cover_url": summary.get("cover_url"), "cover_tone": summary.get("cover_tone"), "stats": summary.get("stats")}


@router.put("/projects/{pid}")
def update_project(pid: str, payload: dict):
    """允许修改 name / description / status / owner / cover_id。"""
    data = _read_project(pid)
    if "name" in payload and payload["name"]:
        data["name"] = payload["name"].strip()
    if "description" in payload:
        data["description"] = (payload["description"] or "").strip()
    if "status" in payload and payload["status"] in VALID_STATUS:
        data["status"] = payload["status"]
    if "owner" in payload and isinstance(payload["owner"], dict):
        owner_name = (payload["owner"].get("name") or "").strip()
        if owner_name:
            data["owner"] = {
                "name": owner_name,
                "initial": (payload["owner"].get("initial") or owner_name[:1] or "?").upper()[:2],
            }
    if "cover_id" in payload:
        cid = payload["cover_id"]
        data["cover_id"] = cid if _valid_cover_id(cid) else data.get("cover_id")
    if "poster_strategy" in payload:
        if payload["poster_strategy"] is None:
            data.pop("poster_strategy", None)
        elif isinstance(payload["poster_strategy"], dict):
            data["poster_strategy"] = sanitize_rich_payload(payload["poster_strategy"])
    if "project_type" in payload:
        data["project_type"] = payload.get("project_type")
    if "scene" in payload:
        data["scene"] = payload.get("scene")
    _write_project(pid, data)
    return _summary(data)


@router.delete("/projects/{pid}")
def delete_project(pid: str):
    pdir = _project_dir(pid)
    if not pdir.exists():
        raise HTTPException(404, f"项目不存在: {pid}")
    shutil.rmtree(pdir, ignore_errors=True)
    return {"ok": True, "id": pid}


@router.get("/projects/{pid}/function-projects/{function_id}")
def list_function_projects(pid: str, function_id: str):
    data = _read_project(pid)
    items = [_function_project_summary(x) for x in _function_projects(data, function_id)]
    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return {"items": items}


@router.post("/projects/{pid}/function-projects/{function_id}")
def create_function_project(pid: str, function_id: str, payload: dict):
    data = _read_project(pid)
    incoming = payload.get("items") if isinstance(payload.get("items"), list) else [payload]
    items = _function_projects(data, function_id)
    created = []
    for raw in incoming:
        if not isinstance(raw, dict):
            continue
        strategy = sanitize_rich_payload(raw.get("poster_strategy")) if isinstance(raw.get("poster_strategy"), dict) else None
        default_name = strategy.get("recognition", {}).get("title") if strategy else ""
        name = (raw.get("name") or default_name or "海报项目").strip()
        item = {
            "id": _gen_function_project_id(function_id),
            "function_id": function_id,
            "name": name or "海报项目",
            "description": (raw.get("description") or "").strip(),
            "status": raw.get("status") or "in_progress",
            "project_type": raw.get("project_type") or (strategy or {}).get("project_type", {}).get("id"),
            "scene": raw.get("scene") or (strategy or {}).get("scene", {}).get("id"),
            "poster_strategy": strategy,
            "source": raw.get("source") or {},
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        items.append(item)
        created.append(_function_project_summary(item))
    _write_project(pid, data)
    return {"items": created}


@router.put("/projects/{pid}/function-projects/{function_id}/{item_id}")
def update_function_project(pid: str, function_id: str, item_id: str, payload: dict):
    data = _read_project(pid)
    items = _function_projects(data, function_id)
    item = next((x for x in items if x.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, f"功能项目不存在: {item_id}")
    for key in ["name", "description", "status", "project_type", "scene"]:
        if key in payload:
            item[key] = payload.get(key)
    if "poster_strategy" in payload and isinstance(payload.get("poster_strategy"), dict):
        strategy = sanitize_rich_payload(payload["poster_strategy"])
        item["poster_strategy"] = strategy
        item["project_type"] = strategy.get("project_type", {}).get("id") or item.get("project_type")
        item["scene"] = strategy.get("scene", {}).get("id") or item.get("scene")
    item["updated_at"] = _now_iso()
    _write_project(pid, data)
    return _function_project_summary(item)


@router.delete("/projects/{pid}/function-projects/{function_id}/{item_id}")
def delete_function_project(pid: str, function_id: str, item_id: str):
    data = _read_project(pid)
    items = _function_projects(data, function_id)
    next_items = [x for x in items if x.get("id") != item_id]
    if len(next_items) == len(items):
        raise HTTPException(404, f"功能项目不存在: {item_id}")
    data.setdefault("function_projects", {})[function_id] = next_items
    _write_project(pid, data)
    return {"ok": True, "id": item_id}


def _extract_json_object(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
      lines = text.splitlines()
      if lines and lines[0].startswith("```"):
          lines = lines[1:]
      if lines and lines[-1].strip() == "```":
          lines = lines[:-1]
      text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            return json.loads(text[start:end + 1])
        raise


def _compact_module_for_copy(module: dict) -> dict:
    cfg = module.get("module_config") or {}
    return {
        "id": module.get("id"),
        "script_key": module.get("script_key"),
        "name": module.get("name") or module.get("display_name"),
        "module_title": cfg.get("module_title") or module.get("name") or module.get("display_name"),
        "purpose": module.get("purpose"),
        "component": module.get("component"),
        "required": bool(module.get("required")),
        "existing_content": cfg.get("content") or "",
        "existing_subsections": cfg.get("subsections") or [],
        "existing_headers": cfg.get("headers") or [],
        "existing_rows": cfg.get("rows") or [],
    }


def _module_copy_schema_hint() -> str:
    return """
模块字段规范：
- M1/M2/M4：使用 content；M2 可把重点词写入 list_items 或直接在 content 中分行。
- M3/M14/M15：优先使用 subsections 或 list_items；M3 是小标题+正文，M14/M15 是名单。
- M5：必须输出 headers 和 rows，保持表格关系。
- M6/M8/M9：输出 content，可补 images 的图片说明，但不要虚构路径。
- M7：输出 submodules，每个子模块可以是评分、学员反馈、图文反馈、收获建议。
- M10：输出 speaker，含 name/title/sections；适合单个讲师或嘉宾深度介绍。
- M11/M12/M13：输出 people_groups，含分组 title、columns、items[name/org/avatar]。
- M16/M17/M18：输出 items，每个 item 是课程/讲师卡片，含 title/text/layout/actions。
- M19：输出 items[label,score,max]，如果知识库没有明确分数，不要编造分数，可给 notes。
- M20/M21：输出 content 和 images 说明，图片路径留空。
- M22/M23：输出 actions[text,hint,color]。
- M24：输出 content 或 contacts。
- M25：输出 content、images 或 qr_image 说明，二维码路径留空。
"""


def _copy_update_to_markdown(update: dict) -> list[str]:
    title = update.get("module_title") or update.get("module_id") or "模块"
    lines = ["", f"## {title}"]
    content = str(update.get("content") or "").strip()
    if content:
        lines.extend(["", content])
    for section in update.get("subsections") or []:
        if not isinstance(section, dict):
            continue
        section_title = str(section.get("title") or "小标题").strip()
        text = str(section.get("text") or "").strip()
        lines.extend(["", f"### {section_title}"])
        if text:
            lines.extend(["", text])
    headers = update.get("headers") or []
    rows = update.get("rows") or []
    if isinstance(headers, list) and headers and isinstance(rows, list):
        safe_headers = [str(h or "") for h in headers]
        lines.extend(["", "| " + " | ".join(safe_headers) + " |"])
        lines.append("| " + " | ".join(["---"] * len(safe_headers)) + " |")
        for row in rows:
            if not isinstance(row, list):
                row = []
            cells = [str(row[i] if i < len(row) else "") for i in range(len(safe_headers))]
            lines.append("| " + " | ".join(cells) + " |")
    for group in update.get("people_groups") or []:
        if not isinstance(group, dict):
            continue
        group_title = str(group.get("title") or "人员分组").strip()
        lines.extend(["", f"### {group_title}"])
        for person in group.get("items") or []:
            if not isinstance(person, dict):
                continue
            name = str(person.get("name") or "姓名").strip()
            org = str(person.get("org") or "").strip()
            avatar = str(person.get("avatar") or "").strip()
            lines.append(f"- {name}{'｜' + org if org else ''}{'' if avatar else ' 【图片】'}")
    speaker = update.get("speaker")
    if isinstance(speaker, dict) and any(speaker.get(k) for k in ("name", "title", "sections", "avatar")):
        name = str(speaker.get("name") or "讲师").strip()
        speaker_title = str(speaker.get("title") or "").strip()
        avatar = str(speaker.get("avatar") or "").strip()
        lines.extend(["", f"### {name}{'｜' + speaker_title if speaker_title else ''}{'' if avatar else '【图片】'}"])
        for section in speaker.get("sections") or []:
            if not isinstance(section, dict):
                continue
            lines.extend(["", f"#### {section.get('title') or '介绍'}"])
            if section.get("text"):
                lines.append(str(section.get("text")))
    for item in update.get("items") or []:
        if not isinstance(item, dict):
            continue
        item_title = str(item.get("title") or "卡片").strip()
        text = str(item.get("text") or "").strip()
        image = str(item.get("image") or "").strip()
        lines.extend(["", f"### {item_title}"])
        if not image:
            lines.append("【图片】")
        if text:
            lines.append(text)
    for action in update.get("actions") or []:
        if not isinstance(action, dict):
            continue
        text = str(action.get("text") or "").strip()
        hint = str(action.get("hint") or "").strip()
        if text or hint:
            lines.extend(["", f"【按钮】{text}{' ' + hint if hint else ''}".strip()])
    for contact in update.get("contacts") or []:
        if not isinstance(contact, dict):
            continue
        label = str(contact.get("label") or "").strip()
        value = str(contact.get("value") or "").strip()
        if label or value:
            lines.append(f"- {label}：{value}" if label else f"- {value}")
    return lines


def _copy_draft_markdown(project: dict, item: dict, title: str, subtitle: str, updates: list) -> str:
    lines = [f"# {title or item.get('name') or project.get('name') or '海报文案'}"]
    if subtitle:
        lines.extend(["", f"> {subtitle}"])
    lines.extend(["", f"对应项目：{project.get('name') or ''}", f"对应海报子项目：{item.get('name') or ''}"])
    for update in updates:
        if isinstance(update, dict):
            lines.extend(_copy_update_to_markdown(update))
    return "\n".join(lines).strip() + "\n"


def _project_kb_context_for_copy(project: dict, module_plan: list[dict], kb_module, top_k: int = 12) -> str:
    pid = project.get("id")
    if not pid:
        return ""
    titles = " ".join(
        str((m.get("module_config") or {}).get("module_title") or m.get("name") or "")
        for m in module_plan if isinstance(m, dict)
    )
    query = f"{project.get('name', '')} {project.get('description', '')} {titles} 项目介绍 培养对象 培养方式 时间节点 课程安排 讲师 报名 联系方式"
    docs = kb_module.search(
        query,
        scope="project",
        project_id=pid,
        top_k=top_k,
        include_global_when_project=False,
    )
    return "\n\n".join(
        f"【{d.get('filename', '?')}】\n{d.get('text', '').strip()}"
        for d in docs
    )


@router.post("/projects/{pid}/function-projects/{function_id}/{item_id}/autofill-modules")
async def autofill_function_project_modules(
    pid: str,
    function_id: str,
    item_id: str,
    module_plan_json: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """用上传文档 + LLM 按当前模块编排生成字段填充建议。

    不直接写项目文件，前端合并后由用户保存。
    """
    data = _read_project(pid)
    item = next((x for x in _function_projects(data, function_id) if x.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, f"功能项目不存在: {item_id}")
    if not files:
        raise HTTPException(400, "请上传至少一份文案资料")
    try:
        module_plan = json.loads(module_plan_json)
    except Exception:
        raise HTTPException(400, "module_plan_json 不是合法 JSON")
    if not isinstance(module_plan, list):
        raise HTTPException(400, "module_plan_json 必须是模块数组")

    import llm_client
    from kb.loader import load as load_doc, SUPPORTED_EXTS, IMAGE_EXTS

    try:
        llm = llm_client.LLMClient()
        if not llm.is_configured:
            raise HTTPException(503, "LLM 未配置：请先在设置抽屉配置大语言模型")
    except llm_client.LLMError as e:
        raise HTTPException(503, str(e))

    tmp_dir = _project_dir(pid) / "_tmp_autofill" / f"tmp_{uuid.uuid4().hex[:8]}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    text_parts = []
    image_refs = []
    try:
        for f in files:
            raw_name = pathlib.Path(f.filename or "untitled").name
            ext = pathlib.Path(raw_name).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            content = await f.read()
            fp = tmp_dir / f"{uuid.uuid4().hex[:8]}{ext}"
            fp.write_bytes(content)
            if ext in IMAGE_EXTS:
                image_refs.append({"name": raw_name, "kind": "uploaded_image"})
            try:
                loaded = load_doc(fp)
                if loaded:
                    text_parts.append(f"【文件：{raw_name}】\n{loaded}")
            except Exception as e:
                text_parts.append(f"【文件：{raw_name}】\n[解析失败：{e}]")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    source_text = "\n\n".join(text_parts).strip()
    if not source_text:
        raise HTTPException(400, "上传资料暂未提取到可识别文本")

    compact_modules = []
    for m in module_plan:
        if not isinstance(m, dict):
            continue
        cfg = m.get("module_config") or {}
        compact_modules.append({
            "id": m.get("id"),
            "script_key": m.get("script_key"),
            "module_title": cfg.get("module_title") or m.get("name") or m.get("display_name"),
            "component": m.get("component"),
        })

    prompt = f"""
你是培训海报文案结构化助手。请把资料原文忠实填入现有海报模块，不新增模块、不删除模块、不改模块顺序。

规则：
1. 只能使用资料中明确出现的内容；不要扩写、不要总结成新意思。
2. 如果资料中有与模块标题完全或近似对应的小标题，优先填入对应模块。
3. 讲师/嘉宾/学员头像墙：识别姓名、职位/组织/头衔、分组标题；没有头像文件路径时 avatar 留空。
4. 单人讲师卡：识别姓名、头衔、头像占位、经历背景、研究方向、课程亮点等段落。
5. 表格模块：识别为 headers 和 rows，复杂表格也尽量保持原行列关系，不要挪位置。
6. 图文/图片模块：文字填 content；图片只能引用 uploaded_images 里已有文件名，不要虚构路径。
7. 返回严格 JSON，不要 markdown。

当前海报子项目：{item.get("name") or ""}
当前模块：
{json.dumps(compact_modules, ensure_ascii=False, indent=2)}

可用上传图片文件名：
{json.dumps(image_refs, ensure_ascii=False, indent=2)}

资料原文：
{source_text[:50000]}

返回格式：
{{
  "updates": [
    {{
      "module_id": "模块 id",
      "module_title": "模块标题",
      "content": "普通正文，可为空",
      "subsections": [{{"title":"小标题","text":"原文内容"}}],
      "headers": ["表头1", "表头2"],
      "rows": [["单元格1", "单元格2"]],
      "people_groups": [{{"title":"分组标题","items":[{{"name":"姓名","org":"组织/头衔","avatar":""}}]}}],
      "speaker": {{"name":"姓名","title":"头衔","avatar":"","sections":[{{"title":"段落标题","text":"原文内容"}}]}},
      "images": [{{"name":"上传图片文件名","path":"","asset_label":"图片说明"}}],
      "confidence": 0.0
    }}
  ],
  "notes": ["无法匹配或需要人工确认的点"]
}}
"""
    try:
        resp = llm.chat(
            [
                {"role": "system", "content": "你只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            timeout=180,
        )
    except llm_client.LLMError as e:
        raise HTTPException(502, f"LLM 调用失败：{e}")

    raw = resp.get("content") or ""
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        parsed = json.loads(raw[start:end + 1] if start >= 0 and end >= start else raw)
    except Exception:
        raise HTTPException(502, f"LLM 未返回合法 JSON：{raw[:500]}")

    updates = parsed.get("updates") if isinstance(parsed, dict) else None
    if not isinstance(updates, list):
        raise HTTPException(502, "LLM JSON 缺少 updates 数组")
    return {
        "updates": updates,
        "notes": parsed.get("notes") or [],
        "source_files": [pathlib.Path(f.filename or "untitled").name for f in files],
    }


@router.post("/projects/{pid}/function-projects/{function_id}/{item_id}/generate-copy")
def generate_function_project_copy(
    pid: str,
    function_id: str,
    item_id: str,
    payload: dict,
):
    """基于项目知识库 + 当前 M1-M25 模块计划生成模块化文案草稿。

    只返回草稿，不直接写回项目；用户确认后由前端合并到模块配置。
    """
    data = _read_project(pid)
    item = next((x for x in _function_projects(data, function_id) if x.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, f"功能项目不存在: {item_id}")

    module_plan = payload.get("module_plan")
    if not isinstance(module_plan, list):
        strategy = item.get("poster_strategy") or {}
        module_plan = strategy.get("module_plan") or []
    if not isinstance(module_plan, list) or not module_plan:
        raise HTTPException(400, "当前海报子项目没有可生成文案的模块计划")

    import llm_client
    from kb import index as kb_index

    try:
        llm = llm_client.LLMClient()
        if not llm.is_configured:
            raise HTTPException(503, "LLM 未配置：请先在设置抽屉配置大语言模型")
    except llm_client.LLMError as e:
        raise HTTPException(503, str(e))

    strategy = payload.get("project_strategy") if isinstance(payload.get("project_strategy"), dict) else (item.get("poster_strategy") or {})
    strategy_type = strategy.get("project_type") or {}
    strategy_scene = strategy.get("scene") or {}
    user_requirement = (payload.get("requirement") or "").strip() or "无"
    overwrite_mode = payload.get("overwrite_mode") or "fill_empty"
    compact_modules = [
        _compact_module_for_copy(m)
        for m in module_plan
        if isinstance(m, dict) and not str(m.get("script_key") or "").startswith("module.tm")
    ]
    if not compact_modules:
        raise HTTPException(400, "当前模块计划只有视觉层，没有可生成文案的 M 模块")

    kb_context = _project_kb_context_for_copy(data, module_plan, kb_index, top_k=14)
    if not kb_context.strip():
        raise HTTPException(400, "项目知识库暂无可用于生成文案的资料，请先上传项目介绍、培养对象、时间节点等资料")

    prompt = f"""
你是腾讯 IEG 人才发展项目的海报文案策划助手。你的任务不是自由写一整篇文章，而是基于项目知识库，为当前海报子项目的 M1-M25 模块生成可编辑的模块化文案草稿。

硬性规则：
1. 必须以项目知识库为事实来源，不能编造项目名称、时间、讲师、报名方式、评分、人数、地点、二维码等事实。
2. 必须严格按给定 module_plan 输出，不新增模块、不删除模块、不改模块顺序。
3. 输出的是“草稿”，用户会先编辑确认，再填入生图模块；所以每个模块要清晰、可改、短而适合海报。
4. 如果知识库信息不足，相关字段留空，并在 notes 中说明缺什么。
5. 如果模块已有用户填写内容，overwrite_mode={overwrite_mode}：
   - fill_empty：已有内容不重写，只给空模块生成。
   - overwrite_all：可全部重写，但不得丢失事实。
6. 返回严格 JSON，不要 markdown，不要解释。

项目：
- 名称：{data.get("name") or ""}
- 简介：{data.get("description") or ""}
- 海报子项目：{item.get("name") or ""}
- 项目类型：{strategy_type.get("label") or item.get("project_type") or ""}
- 海报场景：{strategy_scene.get("label") or item.get("scene") or ""}
- 逻辑链路：{strategy_scene.get("logic_chain") or ""}
- 用户补充要求：{user_requirement}

{_module_copy_schema_hint()}

当前模块计划：
{json.dumps(compact_modules, ensure_ascii=False, indent=2)}

项目知识库摘录：
{kb_context[:60000]}

返回格式：
{{
  "title": "海报主标题建议",
  "subtitle": "海报副标题建议",
  "updates": [
    {{
      "module_id": "模块 id",
      "script_key": "module.m1_text",
      "module_title": "模块标题",
      "content": "普通正文，可为空",
      "subsections": [{{"title":"小标题","text":"正文"}}],
      "list_items": ["条目"],
      "headers": ["表头1", "表头2"],
      "rows": [["单元格1", "单元格2"]],
      "people_groups": [{{"title":"分组标题","columns":5,"items":[{{"name":"姓名","org":"组织/头衔","avatar":""}}]}}],
      "speaker": {{"name":"姓名","title":"头衔","avatar":"","sections":[{{"title":"经历背景","text":"正文"}}]}},
      "items": [{{"title":"卡片标题","text":"正文","layout":"left_image_right_text","actions":[]}}],
      "actions": [{{"text":"按钮文案","hint":"说明","color":""}}],
      "contacts": [{{"label":"联系人","value":"姓名/邮箱/电话"}}],
      "confidence": 0.0
    }}
  ],
  "notes": ["需要人工补充或确认的点"]
}}
"""
    try:
        resp = llm.chat(
            [
                {"role": "system", "content": "你只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.35,
            timeout=220,
        )
    except llm_client.LLMError as e:
        raise HTTPException(502, f"LLM 调用失败：{e}")

    raw = resp.get("content") or ""
    try:
        parsed = _extract_json_object(raw)
    except Exception:
        raise HTTPException(502, f"LLM 未返回合法 JSON：{raw[:500]}")

    updates = parsed.get("updates") if isinstance(parsed, dict) else None
    if not isinstance(updates, list):
        raise HTTPException(502, "LLM JSON 缺少 updates 数组")
    title = parsed.get("title") or ""
    subtitle = parsed.get("subtitle") or ""

    return {
        "title": title,
        "subtitle": subtitle,
        "readable_markdown": _copy_draft_markdown(data, item, title, subtitle, updates),
        "updates": updates,
        "notes": parsed.get("notes") or [],
        "source": {
            "project_id": pid,
            "function_id": function_id,
            "function_project_id": item_id,
            "kb_scope": "project",
            "overwrite_mode": overwrite_mode,
        },
    }


@router.post("/projects/{pid}/function-projects/{function_id}/{item_id}/copy-chat")
def chat_function_project_copy(
    pid: str,
    function_id: str,
    item_id: str,
    payload: dict,
):
    """文案草稿专用 LLM 对话：修改可读全文，并尽量同步结构化模块稿。"""
    data = _read_project(pid)
    item = next((x for x in _function_projects(data, function_id) if x.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, f"功能项目不存在: {item_id}")

    message = str(payload.get("message") or "").strip()
    if not message:
        raise HTTPException(400, "修改要求为空")
    readable_markdown = str(payload.get("readable_markdown") or "").strip()
    updates = payload.get("updates") or []
    if not readable_markdown and not updates:
        raise HTTPException(400, "当前文案为空，无法修改")

    import llm_client
    try:
        llm = llm_client.LLMClient()
        if not llm.is_configured:
            raise HTTPException(503, "LLM 未配置：请先在设置抽屉配置大语言模型")
    except llm_client.LLMError as e:
        raise HTTPException(503, str(e))

    history = payload.get("history") or []
    compact_history = []
    if isinstance(history, list):
        for m in history[-8:]:
            if isinstance(m, dict):
                role = m.get("role") if m.get("role") in ("user", "assistant") else "user"
                compact_history.append({"role": role, "content": str(m.get("content") or "")[:1200]})

    prompt = f"""
你是腾讯 IEG 人才发展项目的海报文案编辑助手。用户正在编辑某一个海报子项目的文案草稿。

你的任务：
1. 根据用户修改要求，直接改写当前“完整可读文案”。
2. 如果修改会影响具体 M1-M25 模块内容，也同步更新 updates 中对应模块；如果无法可靠同步，可保留原 updates。
3. 必须保留项目事实，不得编造时间、地点、讲师、报名方式、二维码、评分、人数。
4. 不要输出解释性 markdown，只返回严格 JSON。

项目：{data.get("name") or ""}
海报子项目：{item.get("name") or ""}
用户修改要求：{message}

当前标题：{payload.get("title") or ""}
当前副标题：{payload.get("subtitle") or ""}

当前完整可读文案：
{readable_markdown[:50000]}

当前结构化模块 updates：
{json.dumps(updates, ensure_ascii=False)[:60000]}

返回格式：
{{
  "title": "修改后的主标题",
  "subtitle": "修改后的副标题",
  "readable_markdown": "修改后的完整可读文案，保留 Markdown 层级、表格和【图片】占位",
  "updates": [{{"module_id":"...", "module_title":"...", "content":"..."}}],
  "reply": "一句话说明已经改了什么"
}}
"""
    messages = [{"role": "system", "content": "你只输出合法 JSON。"}]
    messages.extend(compact_history)
    messages.append({"role": "user", "content": prompt})
    try:
        resp = llm.chat(messages, temperature=0.25, timeout=180)
    except llm_client.LLMError as e:
        raise HTTPException(502, f"LLM 调用失败：{e}")
    raw = resp.get("content") or ""
    try:
        parsed = _extract_json_object(raw)
    except Exception:
        raise HTTPException(502, f"LLM 未返回合法 JSON：{raw[:500]}")
    out_markdown = str(parsed.get("readable_markdown") or "").strip()
    if not out_markdown:
        raise HTTPException(502, "LLM 返回为空，未能生成修改后的文案")
    out_updates = parsed.get("updates")
    return {
        "title": parsed.get("title") or payload.get("title") or "",
        "subtitle": parsed.get("subtitle") or payload.get("subtitle") or "",
        "readable_markdown": out_markdown,
        "updates": out_updates if isinstance(out_updates, list) else updates,
        "reply": parsed.get("reply") or "已按你的要求修改当前文案。",
    }



# ============================================================
# Poster strategy registry: project type -> scene -> module plan
# ============================================================
@router.get("/poster-strategies")
def list_poster_strategies():
    import poster_strategy
    import poster_module_registry
    data = poster_strategy.list_strategies()
    data["default"] = poster_module_registry.enrich_strategy(data["default"])
    data["module_registry"] = poster_module_registry.list_registry()
    return data


@router.post("/poster-strategies/resolve")
def resolve_poster_strategy(payload: dict):
    import poster_strategy
    import poster_module_registry
    strategy = poster_strategy.resolve_strategy(
        payload.get("project_type"),
        payload.get("scene"),
    )
    return poster_module_registry.enrich_strategy(strategy)


@router.get("/poster-module-registry")
def list_poster_module_registry():
    import poster_module_registry
    return poster_module_registry.list_registry()


@router.get("/poster-layout-specs")
def list_poster_layout_specs():
    import poster_layout_specs
    return poster_layout_specs.list_layout_specs()


# ============================================================
# Skill 注册表 + 调用（v0.4 新增）
# ============================================================
@router.get("/skills")
def list_skills():
    """前端动态渲染 skill 表单用。"""
    from skills.registry import list_skills as _list
    return _list()


@router.post("/projects/{pid}/skills/{skill}")
def run_skill(pid: str, skill: str, payload: dict):
    """SSE 流式调用某个 skill，落盘 artifact。
    payload: {params: {...}}
    返回：text/event-stream
    """
    from fastapi.responses import StreamingResponse
    from skills import runner
    from skills.registry import get_skill
    import llm_client
    from kb import index as kb_index

    skill_meta = get_skill(skill)
    if not skill_meta:
        raise HTTPException(404, f"skill 不存在: {skill}")

    # 校验项目
    data = _read_project(pid)

    # 校验必填字段
    params = payload.get("params") or {}
    for f in skill_meta.get("form", []):
        if f.get("required") and not params.get(f["key"]):
            raise HTTPException(400, f"缺少必填字段: {f['label']}（{f['key']}）")

    # LLM 检查
    try:
        llm = llm_client.LLMClient()
        if not llm.is_configured:
            raise HTTPException(503, "LLM 未配置：请在 ⚙️ 设置抽屉填入 DeepSeek API Key")
    except llm_client.LLMError as e:
        raise HTTPException(503, str(e))

    project_dir = _project_dir(pid)

    def _generate():
        for chunk in runner.stream_skill(
            pid=pid,
            skill=skill,
            params=params,
            project=data,
            project_dir=project_dir,
            llm=llm,
            kb_module=kb_index,
        ):
            yield chunk

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁止 nginx 缓冲
        },
    )


# ============================================================
# 编辑器：保存当前 brief 为项目 artifact（v0.4 编辑闭环）
# ============================================================
@router.post("/projects/{pid}/save-as-artifact")
def save_brief_as_artifact(pid: str, payload: dict):
    """编辑器修改完后保存：渲染 PNG + 落 artifact。
    payload: {brief: {...}}
    返回：{artifact}
    """
    import sys
    import time as _time
    import datetime as _dt

    data = _read_project(pid)
    brief = sanitize_rich_payload(payload.get("brief") or {})
    if not isinstance(brief, dict) or not brief.get("sections"):
        raise HTTPException(400, "brief 不合法或为空")

    # 调 skill 引擎渲染
    WEB_ROOT = pathlib.Path(__file__).resolve().parents[1]
    PACKAGE_ROOT = WEB_ROOT.parent
    SKILL_DIR = PACKAGE_ROOT / "gaming-training-poster"
    SCRIPTS_DIR = SKILL_DIR / "scripts"
    sys.path.insert(0, str(SCRIPTS_DIR))
    from compose_poster_v2 import compose_long_poster  # type: ignore

    pdir = _project_dir(pid)
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    aid = f"art_{uuid.uuid4().hex[:10]}"
    art_dir = pdir / "artifacts" / "poster_render" / ts
    art_dir.mkdir(parents=True, exist_ok=True)

    out_png = art_dir / "poster.png"
    t0 = _time.time()
    try:
        compose_long_poster(brief, str(out_png))
    except Exception as e:
        import traceback
        # 失败时回滚
        shutil.rmtree(art_dir, ignore_errors=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"渲染失败：{e}", "traceback": traceback.format_exc()[:1500]},
        )
    dt = _time.time() - t0

    if not out_png.exists():
        shutil.rmtree(art_dir, ignore_errors=True)
        raise HTTPException(500, "引擎运行后未产出 PNG")

    # 缩略图
    try:
        from PIL import Image
        full = Image.open(out_png)
        ratio = 720 / full.width
        thumb = full.resize((720, int(full.height * ratio)), Image.LANCZOS)
        thumb.convert("RGB").save(art_dir / "cover.jpg", "JPEG", quality=82, optimize=True)
    except Exception:
        pass

    # 落 brief.json
    (art_dir / "output.json").write_text(
        json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    files = [f.name for f in art_dir.iterdir() if f.is_file()]

    artifact = {
        "id": aid,
        "skill": "poster_render",
        "title": f"编辑器版本 v{len([a for a in data.get('artifacts',[]) if a.get('skill')=='poster_render'])+1}",
        "path": f"artifacts/poster_render/{ts}/",
        "files": files,
        "created_at": _now_iso(),
        "duration_sec": round(dt, 2),
    }

    data.setdefault("artifacts", []).insert(0, artifact)
    _write_project(pid, data)

    return {"artifact": artifact}


@router.post("/projects/{pid}/function-projects/{function_id}/{item_id}/copy-artifact")
def save_function_project_copy_artifact(pid: str, function_id: str, item_id: str, payload: dict):
    data = _read_project(pid)
    items = _function_projects(data, function_id)
    item = next((x for x in items if x.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, f"功能项目不存在: {item_id}")

    markdown = str(payload.get("markdown") or "").strip()
    module_markdown = str(payload.get("module_markdown") or "").strip()
    updates = sanitize_rich_payload(payload.get("updates") or [])
    if not markdown and not updates:
        raise HTTPException(400, "文案内容为空，无法保存")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    aid = f"art_{uuid.uuid4().hex[:10]}"
    art_dir = _project_dir(pid) / "artifacts" / "copywriter" / ts
    art_dir.mkdir(parents=True, exist_ok=True)

    if markdown:
        (art_dir / "output.md").write_text(markdown, encoding="utf-8")
    output_json = {
        "title": payload.get("title") or item.get("name") or data.get("name") or "海报文案",
        "subtitle": payload.get("subtitle") or "",
        "project_id": pid,
        "function_id": function_id,
        "function_project_id": item_id,
        "function_project_name": item.get("name"),
        "readable_markdown": markdown,
        "module_markdown": module_markdown,
        "module_copy": updates,
        "updates": updates,
        "notes": payload.get("notes") or [],
    }
    (art_dir / "output.json").write_text(
        json.dumps(output_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    files = [f.name for f in art_dir.iterdir() if f.is_file()]
    artifact = {
        "id": aid,
        "skill": "copywriter",
        "title": f"{item.get('name') or '海报子项目'} 文案稿",
        "path": f"artifacts/copywriter/{ts}/",
        "files": files,
        "created_at": _now_iso(),
        "params": {
            "function_id": function_id,
            "function_project_id": item_id,
        },
    }
    data.setdefault("artifacts", []).insert(0, artifact)
    item["copy_artifact_id"] = aid
    item["copy_updated_at"] = artifact["created_at"]
    item["updated_at"] = artifact["created_at"]
    data["updated_at"] = artifact["created_at"]
    _write_project(pid, data)
    return {"artifact": artifact, "function_project": _function_project_summary(item)}


# ============================================================
# Artifact 访问（细化由后续阶段 C/D/E 落实，这里先放只读取）
# ============================================================
@router.get("/projects/{pid}/artifacts/{aid}")
def get_artifact(pid: str, aid: str):
    """根据 artifact id 返回元数据 + 主输出内容（output.md / output.json）。"""
    data = _read_project(pid)
    art = next((a for a in (data.get("artifacts") or []) if a.get("id") == aid), None)
    if not art:
        raise HTTPException(404, f"产物不存在: {aid}")
    pdir = _project_dir(pid)
    art_dir = pdir / art["path"]
    output = {}
    md_fp = art_dir / "output.md"
    json_fp = art_dir / "output.json"
    if md_fp.exists():
        output["markdown"] = md_fp.read_text(encoding="utf-8")
    if json_fp.exists():
        try:
            output["json"] = json.loads(json_fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"meta": art, "output": output}


@router.get("/projects/{pid}/artifacts/{aid}/file")
def get_artifact_file(pid: str, aid: str, name: str = "cover.png"):
    """直接取产物目录下的某个文件（图片预览等）。"""
    data = _read_project(pid)
    art = next((a for a in (data.get("artifacts") or []) if a.get("id") == aid), None)
    if not art:
        raise HTTPException(404, f"产物不存在: {aid}")
    if "/" in name or ".." in name:
        raise HTTPException(400, "非法文件名")
    fp = _project_dir(pid) / art["path"] / name
    if name == "poster.pdf" and not fp.exists():
        png_fp = _project_dir(pid) / art["path"] / "poster.png"
        if png_fp.exists():
            try:
                Image.open(png_fp).convert("RGB").save(fp, "PDF", resolution=300.0)
            except Exception as e:
                raise HTTPException(500, f"PDF 导出失败: {e}")
    if not fp.exists():
        raise HTTPException(404, f"文件不存在: {name}")
    return FileResponse(fp)
