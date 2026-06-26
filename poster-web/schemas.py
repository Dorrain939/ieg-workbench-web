"""Section type → 表单字段映射。前端按 schema 动态生成控件。"""

import asset_types

# 字段控件类型说明：
#   text     → 单行输入框
#   textarea → 多行
#   number   → 数字输入（min/max）
#   select   → 下拉
#   color    → 色块选择 + 色值输入
#   bool     → 开关
#   file     → 文件选择（前端会调上传 API 或选既有素材）
#   array    → 字符串数组（每行一项的 textarea）
#   matrix   → 二维数组表格（rows×cols 输入网格）
#   members  → 讲师团成员列表（专用控件）
#   bullets  → notice_box 多 bullet（支持单条 highlight）

# ============================================================
# Canvas 全局字段
# ============================================================
CANVAS_SCHEMA = [
    {"key": "width", "label": "画布宽度", "type": "number",
     "min": 1200, "max": 1440, "default": 1440},
    {"key": "scene", "label": "场景", "type": "select",
     "options": [
         {"value": "S1", "label": "S1 · 新人朝气（极光蓝紫/像素暖晨光/星云蓝）"},
         {"value": "S2", "label": "S2 · 领导力沉稳（深空藏蓝/炭黑金）"},
         {"value": "S3", "label": "S3 · 技术分享（霓虹赛博/引擎核心）"},
         {"value": "S4", "label": "S4 · 嘉年华文化（糖果色/夕阳街机/朱红暖金）"},
         {"value": "S5", "label": "S5 · 晋升表彰（丝绒金/水墨荣耀）"},
         {"value": "S6", "label": "S6 · 电竞赛事（竞技场/电路火焰）"},
     ], "default": "S3"},
    {"key": "palette_strategy", "label": "配色方案", "type": "select",
     "options": [
         {"value": "named:aurora", "label": "极光蓝紫（S1 新人朝气）"},
         {"value": "named:pixel_dawn", "label": "像素暖晨光（S1）"},
         {"value": "named:nebula_blue", "label": "星云蓝（S1）"},
         {"value": "named:deep_space", "label": "深空藏蓝 + 古铜金（S2 领导力）"},
         {"value": "named:charcoal_gold", "label": "炭黑 + 勋章金（S2）"},
         {"value": "named:cyber_neon", "label": "霓虹赛博紫（S3 技术分享）"},
         {"value": "named:engine_core", "label": "引擎核心荧光绿（S3）"},
         {"value": "named:carnival", "label": "嘉年华糖果色（S4 文化活动）"},
         {"value": "named:sunset_arcade", "label": "夕阳街机（S4）"},
         {"value": "named:festival_red", "label": "朱红暖金（S4 节日）"},
         {"value": "named:velvet_gold", "label": "丝绒金（S5 晋升表彰）"},
         {"value": "named:ink_honor", "label": "水墨荣耀（S5）"},
         {"value": "named:arena", "label": "电竞竞技场（S6 赛事）"},
         {"value": "named:circuit_flame", "label": "电路火焰（S6）"},
         {"value": "auto_bright", "label": "自动 · 亮色"},
         {"value": "auto_dark", "label": "自动 · 暗色"},
     ], "default": "named:cyber_neon"},
    {"key": "bg_colors", "label": "底色渐变 (2 个色值)", "type": "color2",
     "default": ["#1A0A3D", "#0D0520"]},
    {"key": "global_bg_path", "label": "全局底图", "type": "file", "asset_types": ["global_bg"]},
    {"key": "bg_image_path", "label": "头部底图", "type": "file", "asset_types": ["hero_bg"]},
    {"key": "bg_image_bottom_fade_ratio", "label": "底图底部渐变到透明的比例",
     "type": "number", "min": 0.0, "max": 0.6, "step": 0.05, "default": 0.35},
    {"key": "pattern", "label": "底纹", "type": "select",
     "options": [
         {"value": "none", "label": "无"},
         {"value": "grid", "label": "网格"},
         {"value": "dots", "label": "圆点"},
     ], "default": "none"},
    {"key": "glow", "label": "径向光晕", "type": "bool", "default": False},
]

# ============================================================
# Section schemas
# ============================================================
SCHEMAS = {
    # -------- 1. 顶部 logo 横幅 --------
    "top_logo_bar": {
        "label": "顶部 Logo 横幅",
        "icon": "🏷️",
        "fields": [
            {"key": "logos", "label": "Logo 路径列表（每行一个）", "type": "array",
             "default": []},
            {"key": "logo_heights", "label": "每个 Logo 的高度（px，每行一个）", "type": "array",
             "default": [44, 44, 44, 44]},
            {"key": "gap", "label": "Logo 间距", "type": "number", "min": 20, "max": 200, "default": 80},
            {"key": "pad_top", "label": "上边距", "type": "number", "min": 0, "max": 100, "default": 22},
            {"key": "pad_bottom", "label": "下边距", "type": "number", "min": 0, "max": 100, "default": 22},
            {"key": "align", "label": "对齐", "type": "select",
             "options": [
                 {"value": "center", "label": "居中"},
                 {"value": "left", "label": "靠左"},
                 {"value": "right", "label": "靠右"},
             ], "default": "center"},
        ],
    },

    # -------- 2. 主标题艺术字（hero_strip） --------
    "hero_strip": {
        "label": "主标题艺术字",
        "icon": "🎨",
        "fields": [
            {"key": "tight_bottom", "label": "紧贴艺术字底（推荐开启）", "type": "bool", "default": True},
            {"key": "title_card.style", "label": "样式", "type": "select",
             "options": [
                 {"value": "ai_wordart", "label": "艺术字 PNG（推荐）"},
                 {"value": "image", "label": "普通图片"},
             ], "default": "ai_wordart"},
            {"key": "title_card.image", "label": "艺术字图片（透明底或黑底）", "type": "file", "asset_types": ["main_wordart"]},
            {"key": "title_card.chroma_key", "label": "需要抠图（图为黑底时勾选）",
             "type": "bool", "default": False},
            {"key": "title_card.chroma_bg_kind", "label": "抠图背景类型",
             "type": "select", "options": [
                 {"value": "dark", "label": "深色底"},
                 {"value": "light", "label": "浅色底"},
                 {"value": "auto", "label": "自动判断"},
             ], "default": "dark"},
            {"key": "title_card.key_lightness", "label": "抠图阈值（0-100）",
             "type": "number", "min": 0, "max": 200, "default": 50},
            {"key": "title_card.shadow", "label": "阴影", "type": "bool", "default": False},
            {"key": "title_card.width_ratio", "label": "艺术字宽度占比",
             "type": "number", "min": 0.5, "max": 1.0, "step": 0.02, "default": 0.86},
            {"key": "title_card.offset_from_bottom", "label": "距底图底部 px",
             "type": "number", "min": 100, "max": 600, "default": 320},
            {"key": "title_card.safe_zone", "label": "安全区",
             "type": "select", "options": [
                 {"value": "auto", "label": "自动"},
                 {"value": "bottom", "label": "强制下半部"},
                 {"value": "top", "label": "强制上半部"},
             ], "default": "auto"},
        ],
    },

    # -------- 3. 副标题艺术字 --------
    "subtitle_text": {
        "label": "副标题",
        "icon": "✨",
        "fields": [
            {"key": "text", "label": "文字", "type": "text", "default": "正式开营啦！"},
            {"key": "font_size", "label": "字号", "type": "number", "min": 32, "max": 200, "default": 96},
            {"key": "offset_x", "label": "水平偏移（视觉居中微调）",
             "type": "number", "min": -100, "max": 100, "default": 0},
            {"key": "pad_top", "label": "上边距", "type": "number", "min": 0, "max": 60, "default": 0},
            {"key": "pad_bottom", "label": "下边距", "type": "number", "min": 0, "max": 60, "default": 0},
        ],
    },

    # -------- 4. 模块标题 --------
    "section_title_bar": {
        "label": "模块标题",
        "icon": "📌",
        "fields": [
            {"key": "text", "label": "标题文字", "type": "text", "default": "模块标题"},
            {"key": "style", "label": "样式", "type": "select",
             "options": [
                 {"value": "plain", "label": "简洁（白字下划线）"},
                 {"value": "numbered", "label": "带数字编号"},
             ], "default": "plain"},
            {"key": "index", "label": "编号（仅 numbered）", "type": "number", "min": 0, "max": 99, "default": 0},
            {"key": "text_color", "label": "标题颜色", "type": "color", "default": "#FFFFFF"},
            {"key": "underline_color", "label": "下划线颜色", "type": "color", "default": "auto"},
            {"key": "font_size", "label": "字号", "type": "number", "min": 28, "max": 80, "default": 52},
        ],
    },

    # -------- 5. 段落正文 --------
    "lead_paragraph": {
        "label": "段落正文",
        "icon": "📝",
        "fields": [
            {"key": "text", "label": "正文", "type": "textarea", "required": True,
             "default": ""},
            {"key": "panel_style", "label": "面板样式", "type": "select",
             "options": [
                 {"value": "asset_frame", "label": "素材框（用上传的框图）"},
                 {"value": "frosted", "label": "磨砂玻璃"},
                 {"value": "panel_dark", "label": "深色面板"},
                 {"value": "panel_light", "label": "浅色面板"},
                 {"value": "yellow-card", "label": "黄色卡片"},
                 {"value": "none", "label": "无框（直接铺底色）"},
             ],
             "default": "asset_frame"},
            {"key": "asset_frame_path", "label": "素材框（仅 素材框 模式）", "type": "file", "asset_types": ["module_frame"]},
            {"key": "text_color", "label": "文字颜色", "type": "color", "default": "#E8D8FF"},
            {"key": "font_size", "label": "字号", "type": "number", "min": 16, "max": 56, "default": 28},
            {"key": "font_role", "label": "字体/字重", "type": "select",
             "options": [
                 {"value": "body", "label": "正文体 W3"},
                 {"value": "display", "label": "标题粗体 W7"},
             ], "default": "body"},
            {"key": "pad", "label": "内边距", "type": "number", "min": 0, "max": 80, "default": 40},
            {"key": "line_height", "label": "行高（无框模式下生效）",
             "type": "number", "min": 30, "max": 120, "default": 60},
            {"key": "corner", "label": "圆角", "type": "number", "min": 0, "max": 80, "default": 16},
        ],
    },

    # -------- 5b. 要点块 --------
    "bullet_points_block": {
        "label": "要点块",
        "icon": "•",
        "fields": [
            {"key": "bullets", "label": "要点（每行一个）", "type": "array", "default": []},
            {"key": "number_style", "label": "编号样式", "type": "select",
             "options": [
                 {"value": "circle", "label": "圆形编号"},
                 {"value": "square", "label": "方形编号"},
                 {"value": "none", "label": "无编号"},
             ], "default": "circle"},
            {"key": "accent_color", "label": "编号/边框颜色", "type": "color", "default": "auto"},
            {"key": "text_color", "label": "文字颜色", "type": "color", "default": "auto"},
            {"key": "font_size", "label": "字号", "type": "number", "min": 18, "max": 50, "default": 36},
            {"key": "font_role", "label": "字体/字重", "type": "select",
             "options": [
                 {"value": "body", "label": "正文体 W3"},
                 {"value": "display", "label": "标题粗体 W7"},
             ], "default": "display"},
        ],
    },

    # -------- 6. 图片块 --------
    "image_block": {
        "label": "图片块",
        "icon": "🖼️",
        "fields": [
            {"key": "image_path", "label": "图片", "type": "file", "required": True, "asset_types": ["module_content_image"]},
            {"key": "width_ratio", "label": "宽度占比",
             "type": "number", "min": 0.3, "max": 1.0, "step": 0.05, "default": 1.0},
            {"key": "align", "label": "对齐", "type": "select",
             "options": [
                 {"value": "center", "label": "居中"},
                 {"value": "left", "label": "靠左"},
                 {"value": "right", "label": "靠右"},
             ], "default": "center"},
            {"key": "pad_top", "label": "上边距", "type": "number", "min": 0, "max": 80, "default": 8},
            {"key": "pad_bottom", "label": "下边距", "type": "number", "min": 0, "max": 80, "default": 8},
            {"key": "corner_radius", "label": "圆角", "type": "number", "min": 0, "max": 60, "default": 0},
        ],
    },

    # -------- 7. 数据表格 --------
    "data_table": {
        "label": "数据表格",
        "icon": "📊",
        "fields": [
            {"key": "headers", "label": "表头（每行一个，逗号分隔多列）",
             "type": "array", "default": ["时间", "环节"]},
            {"key": "rows", "label": "数据（每行一组，逗号分隔多列）",
             "type": "matrix", "default": [
                ["10:00 - 10:20", "项目介绍"],
                ["10:20 - 10:50", "嘉宾分享"],
             ]},
            {"key": "align", "label": "各列对齐（每行一项）",
             "type": "array", "default": ["center", "center"]},
            {"key": "col_weights", "label": "各列宽度权重（每行一个）",
             "type": "array", "default": [1.0, 1.5]},
            {"key": "accent_color", "label": "强调色（表头底）", "type": "color", "default": "#9333EA"},
            {"key": "header_color", "label": "表头字色", "type": "color", "default": "#FFFFFF"},
            {"key": "header_font_size", "label": "表头字号",
             "type": "number", "min": 18, "max": 50, "default": 34},
            {"key": "font_size", "label": "单元格字号",
             "type": "number", "min": 16, "max": 48, "default": 32},
            {"key": "text_color", "label": "单元格文字颜色", "type": "color", "default": "auto"},
            {"key": "font_role", "label": "单元格字体/字重", "type": "select",
             "options": [
                 {"value": "body", "label": "正文体 W3"},
                 {"value": "display", "label": "标题粗体 W7"},
             ], "default": "body"},
        ],
    },

    # -------- 7b. 复杂表格 --------
    "complex_table": {
        "label": "复杂表格",
        "icon": "▦",
        "fields": [
            {"key": "col_count", "label": "列数", "type": "number", "min": 2, "max": 10, "default": 4},
            {"key": "col_weights", "label": "各列宽度权重（每行一个）",
             "type": "array", "default": [1.0, 1.0, 1.4, 1.4]},
            {"key": "accent_color", "label": "强调色（表头底）", "type": "color", "default": "#9333EA"},
            {"key": "font_size", "label": "单元格字号",
             "type": "number", "min": 16, "max": 36, "default": 24},
            {"key": "pad", "label": "外边距",
             "type": "number", "min": 8, "max": 40, "default": 16},
        ],
    },

    # -------- 8. 讲师 / 顾问团 --------
    "faculty_grid": {
        "label": "讲师团 / 顾问团",
        "icon": "👥",
        "fields": [
            {"key": "members", "label": "成员列表", "type": "members",
             "default": []},
            {"key": "layout", "label": "布局", "type": "select",
             "options": [
                 {"value": "grid", "label": "网格（每行 N 人，推荐）"},
                 {"value": "compact", "label": "紧凑（≤4 人，双列卡片）"},
                 {"value": "default", "label": "默认（5+ 人纵列单行）"},
                 {"value": "detail", "label": "详细（≤2 人大卡）"},
             ], "default": "grid"},
            {"key": "cols", "label": "每行人数（仅 网格 布局）",
             "type": "number", "min": 2, "max": 8, "default": 5},
            {"key": "avatar_shape", "label": "头像形状", "type": "select",
             "options": [
                 {"value": "circle", "label": "圆形"},
                 {"value": "square", "label": "方形"},
             ], "default": "circle"},
            {"key": "avatar_size", "label": "头像尺寸（px）",
             "type": "number", "min": 80, "max": 280, "default": 180},
            {"key": "ring_color", "label": "头像描边色", "type": "color", "default": "#9333EA"},
            {"key": "ring_width", "label": "头像描边宽度",
             "type": "number", "min": 0, "max": 12, "default": 6},
            {"key": "panel_style", "label": "底框样式", "type": "select",
             "options": [
                 {"value": "none", "label": "无底框"},
                 {"value": "asset_frame", "label": "素材框"},
             ], "default": "none"},
            {"key": "asset_frame_path", "label": "底框素材", "type": "file", "asset_types": ["module_frame"]},
            {"key": "frame_inset", "label": "底框内边距",
             "type": "number", "min": 0, "max": 80, "default": 32},
            {"key": "name_color", "label": "姓名颜色", "type": "color", "default": "#FFFFFF"},
            {"key": "title_color", "label": "职务颜色", "type": "color", "default": "#FFFFFF"},
            {"key": "name_font_size", "label": "姓名字号",
             "type": "number", "min": 14, "max": 40, "default": 26},
            {"key": "title_font_size", "label": "职务字号",
             "type": "number", "min": 14, "max": 32, "default": 20},
            {"key": "title_font_role", "label": "职务字重", "type": "select",
             "options": [
                 {"value": "body", "label": "细体 W3"},
                 {"value": "display", "label": "粗体 W7"},
             ], "default": "body"},
            {"key": "max_title_lines", "label": "职务最多行数",
             "type": "number", "min": 1, "max": 5, "default": 3},
            {"key": "gap_x", "label": "横向间距", "type": "number", "min": 0, "max": 80, "default": 24},
            {"key": "gap_y", "label": "纵向间距", "type": "number", "min": 0, "max": 80, "default": 40},
        ],
    },

    # -------- 9. 注意事项 --------
    "notice_box": {
        "label": "注意事项 / 学员须知",
        "icon": "⚠️",
        "fields": [
            {"key": "bullets", "label": "条目（支持单条标红）", "type": "bullets",
             "default": []},
            {"key": "accent_color", "label": "强调色", "type": "color", "default": "#9333EA"},
            {"key": "text_color", "label": "正文颜色", "type": "color", "default": "auto"},
            {"key": "font_size", "label": "字号",
             "type": "number", "min": 18, "max": 48, "default": 32},
            {"key": "font_role", "label": "字体/字重", "type": "select",
             "options": [
                 {"value": "body", "label": "正文体 W3"},
                 {"value": "display", "label": "标题粗体 W7"},
             ], "default": "display"},
        ],
    },

    # -------- 10. 联系方式 --------
    "contact_inline": {
        "label": "联系方式",
        "icon": "📞",
        "fields": [
            {"key": "text", "label": "文案（支持 \\n 换行）", "type": "textarea",
             "default": ""},
            {"key": "text_color", "label": "文字颜色", "type": "color", "default": "auto"},
            {"key": "font_size", "label": "字号",
             "type": "number", "min": 18, "max": 44, "default": 28},
            {"key": "font_role", "label": "字体/字重", "type": "select",
             "options": [
                 {"value": "body", "label": "正文体 W3"},
                 {"value": "display", "label": "标题粗体 W7"},
             ], "default": "display"},
            {"key": "mode", "label": "模式", "type": "select",
             "options": [
                 {"value": "text", "label": "纯文字"},
                 {"value": "qr", "label": "文字 + 二维码"},
             ], "default": "text"},
            {"key": "qr_image", "label": "二维码（仅 二维码 模式）", "type": "file", "asset_types": ["contact_qr"]},
            {"key": "qr_label", "label": "二维码标签", "type": "text", "default": "扫码联系"},
        ],
    },

    # -------- 11. 信息卡（带 logo） --------
    "info_card": {
        "label": "信息卡（机构介绍）",
        "icon": "🏛️",
        "fields": [
            {"key": "heading", "label": "标题（可空）", "type": "text", "default": ""},
            {"key": "body", "label": "正文", "type": "textarea", "required": True, "default": ""},
            {"key": "panel_style", "label": "面板样式", "type": "select",
             "options": [
                 {"value": "asset_frame", "label": "素材框"},
                 {"value": "frosted", "label": "磨砂玻璃"},
                 {"value": "panel_dark", "label": "深色面板"},
             ], "default": "asset_frame"},
            {"key": "asset_frame_path", "label": "素材框", "type": "file", "asset_types": ["module_frame"]},
            {"key": "logo_path", "label": "Logo（左侧）", "type": "file", "asset_types": ["logo_black", "logo_white", "logo_color"]},
            {"key": "logo_height", "label": "Logo 高度", "type": "number", "min": 30, "max": 120, "default": 80},
            {"key": "logo_invert", "label": "反色 Logo（深底用）", "type": "bool", "default": False},
            {"key": "text_color", "label": "文字颜色", "type": "color", "default": "#FFFFFF"},
        ],
    },

    # -------- 12. CTA 按钮 --------
    "cta_button": {
        "label": "CTA 大按钮",
        "icon": "🔘",
        "fields": [
            {"key": "text", "label": "按钮文字", "type": "text", "default": "立即报名"},
            {"key": "pre_lines", "label": "按钮上方文案（每行一项）", "type": "array", "default": []},
            {"key": "post_lines", "label": "按钮下方文案（每行一项）", "type": "array", "default": []},
        ],
    },
}


def all_section_types():
    for meta in SCHEMAS.values():
        asset_types.with_file_asset_types(meta.get("fields", []))
    return list(SCHEMAS.keys())


def get_schema(section_type):
    meta = SCHEMAS.get(section_type)
    if meta and meta.get("fields"):
        asset_types.with_file_asset_types(meta["fields"])
    return meta


def get_canvas_schema():
    return asset_types.with_file_asset_types(CANVAS_SCHEMA)
