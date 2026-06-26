"""Central poster visual asset taxonomy.

These types are shared by uploads, schemas, the editor, and poster skills so
images keep their intended role instead of becoming anonymous image files.
"""
from __future__ import annotations

ASSET_TYPES = [
    {"value": "logo_black", "label": "Logo · 黑色", "group": "logo", "hint": "浅色背景上使用的黑色 Logo"},
    {"value": "logo_white", "label": "Logo · 白色", "group": "logo", "hint": "深色背景上使用的白色 Logo"},
    {"value": "logo_color", "label": "Logo · 彩色", "group": "logo", "hint": "品牌彩色 Logo"},
    {"value": "global_bg", "label": "全局底图", "group": "background", "hint": "整张长图最底层背景"},
    {"value": "global_bg_decoration", "label": "全局底图装饰元素", "group": "background", "hint": "融入全局背景的漂浮/几何装饰"},
    {"value": "hero_bg", "label": "头部底图", "group": "hero", "hint": "海报头部主视觉背景"},
    {"value": "main_wordart", "label": "主标题艺术字图", "group": "hero", "hint": "主标题透明底或可抠图艺术字"},
    {"value": "subtitle_wordart", "label": "副标题艺术字", "group": "hero", "hint": "副标题艺术字图"},
    {"value": "subtitle_decoration", "label": "副标题艺术字装饰", "group": "hero", "hint": "副标题周围的装饰图"},
    {"value": "section_title_decoration", "label": "模块标题装饰图", "group": "module", "hint": "模块标题下划线/角标/贴片装饰"},
    {"value": "module_frame", "label": "模块素材框", "group": "module", "hint": "替换 AI 生成卡片框的真实素材框"},
    {"value": "module_content_image", "label": "模块内容图", "group": "module", "hint": "复杂内容效果不好时使用的整块内容图"},
    {"value": "contact_qr", "label": "联系人二维码", "group": "contact", "hint": "报名/咨询/联系人二维码"},
    {"value": "person_avatar", "label": "人员头像图", "group": "people", "hint": "讲师、学员等头像，需要关联姓名/职称"},
]

ASSET_TYPE_MAP = {item["value"]: item for item in ASSET_TYPES}

FIELD_ASSET_TYPES = {
    "global_bg_path": ["global_bg"],
    "bg_image_path": ["hero_bg"],
    "title_card.image": ["main_wordart"],
    "subtitle_image": ["subtitle_wordart"],
    "subtitle_decoration_path": ["subtitle_decoration"],
    "title_decoration_path": ["section_title_decoration"],
    "asset_frame_path": ["module_frame"],
    "image_path": ["module_content_image"],
    "qr_image": ["contact_qr"],
    "logo_path": ["logo_black", "logo_white", "logo_color"],
    "avatar": ["person_avatar"],
}

ALIASES = {
    "logo": "logo_color",
    "black_logo": "logo_black",
    "white_logo": "logo_white",
    "color_logo": "logo_color",
    "background": "global_bg",
    "global_background": "global_bg",
    "bg": "global_bg",
    "deco": "global_bg_decoration",
    "decoration": "global_bg_decoration",
    "hero": "hero_bg",
    "header_bg": "hero_bg",
    "wordart": "main_wordart",
    "title_wordart": "main_wordart",
    "frame": "module_frame",
    "content_image": "module_content_image",
    "qr": "contact_qr",
    "avatar": "person_avatar",
}

KEYWORD_INFER = [
    ("global_bg_decoration", ["装饰", "deco", "decoration", "decorate"]),
    ("global_bg", ["全局", "底图", "global", "background", "bg"]),
    ("hero_bg", ["头部", "头图", "header", "hero"]),
    ("main_wordart", ["主标题", "艺术字", "wordart", "title"]),
    ("subtitle_wordart", ["副标题", "subtitle"]),
    ("module_frame", ["素材框", "底框", "frame", "card"]),
    ("contact_qr", ["二维码", "qr"]),
    ("person_avatar", ["头像", "avatar", "headshot", "讲师", "学员"]),
    ("logo_white", ["白logo", "白色logo", "white logo", "logo_white"]),
    ("logo_black", ["黑logo", "黑色logo", "black logo", "logo_black"]),
    ("logo_color", ["彩logo", "彩色logo", "color logo", "logo_color", "logo"]),
]


def normalize_asset_type(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "module_content_image"
    raw_l = raw.lower().replace("-", "_").replace(" ", "_")
    if raw_l in ASSET_TYPE_MAP:
        return raw_l
    if raw_l in ALIASES:
        return ALIASES[raw_l]
    return "module_content_image"


def asset_type_label(value: str | None) -> str:
    key = normalize_asset_type(value)
    return ASSET_TYPE_MAP.get(key, {}).get("label", key)


def infer_asset_type(filename: str = "", asset_type: str | None = None) -> str:
    if asset_type:
        return normalize_asset_type(asset_type)
    name = str(filename or "").lower()
    for typ, words in KEYWORD_INFER:
        if any(w.lower() in name for w in words):
            return typ
    return "module_content_image"


def with_file_asset_types(fields: list[dict]) -> list[dict]:
    for f in fields:
        if f.get("type") == "file" and not f.get("asset_types"):
            key = f.get("key") or ""
            if key in FIELD_ASSET_TYPES:
                f["asset_types"] = FIELD_ASSET_TYPES[key]
    return fields
