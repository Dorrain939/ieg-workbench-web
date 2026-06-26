"""AI 训练营主题包 · ai_bootcamp_navy

参考原稿：「IEG AI BOOTCAMP 互娱实战营 第十期」（手机长图海报）
设计语言：深蓝紫科技底（#0A1B3D / #050A1F）+ 荧光黄绿强调（#CBF44E）+ 白字 + 黑色文本卡

提供给 brief 的能力：
- canvas 默认色（bg_colors / palette / pattern / glow）
- course_card 默认配色（编号色 / 主标色 / CTA 色 / bullet 圆点色）
- 文字配色梯度（heading / body / caption）

使用方式：
    {
        "theme": "ai_bootcamp",
        "canvas": { ... },     # 没填的字段自动从主题取默认
        "sections": [...]
    }
"""

THEME = {
    "name": "ai_bootcamp_navy",
    "label": "AI 训练营 · 蓝绿科技",

    # 全局画布默认
    "canvas_defaults": {
        "bg_colors": ["#0A1B3D", "#050A1F"],
        "palette_strategy": "named:cyber_neon",  # 兜底，不影响主题色
        "pattern": "none",
        "glow": False,
        "bg_image_bottom_fade_ratio": 0.30,
    },

    # 调色板（所有组件读这里取色）
    "palette": {
        # 主色
        "bg_primary": "#0A1B3D",       # 深蓝紫底色
        "bg_secondary": "#050A1F",     # 更深底
        "panel_dark": "#0F1F40",       # 深色卡面板
        "panel_darker": "#08152D",     # 卡片更深的内层

        # 强调色
        "accent_lime": "#CBF44E",      # 荧光黄绿（主强调色）
        "accent_lime_dim": "#A8D33A",  # 暗一档黄绿

        # 文字
        "text_primary": "#FFFFFF",     # 主文字（白）
        "text_secondary": "#E0E6F0",   # 次文字（淡蓝白）
        "text_muted": "#8A95B0",       # 弱化文字
        "text_on_lime": "#0A1B3D",     # 黄绿底上的字色（深蓝）

        # 装饰
        "divider": "#1F3260",          # 分隔线
        "border_subtle": "#1A2848",    # 不显眼的边框
    },

    # 字体梯度
    "fonts": {
        "display_w7": "TencentSans-W7.ttf",   # 大标题
        "body_w3": "TencentSans-W3.ttf",      # 正文
    },

    # course_card 默认参数（新组件的样式锁定值）
    "course_card_defaults": {
        "card_padding": 60,
        "index_font_size": 130,            # "01" "02" 大数字
        "index_color": "#CBF44E",
        "index_italic_skew": 0.18,         # 数字假斜体倾斜量
        "title_font_size": 48,             # 课程主标题
        "title_color": "#FFFFFF",
        "instructor_avatar_size": 130,
        "instructor_name_font_size": 32,
        "instructor_name_color": "#FFFFFF",
        "cta_text": "立即报名",
        "cta_bg": "#CBF44E",
        "cta_text_color": "#0A1B3D",
        "cta_font_size": 32,
        "section_label_font_size": 32,     # 「解决痛点」「课程收益」标签
        "section_label_color": "#CBF44E",
        "bullet_font_size": 28,
        "bullet_color": "#E0E6F0",
        "bullet_marker_color": "#CBF44E",
        "meta_font_size": 28,              # 时间/地点
        "meta_color": "#FFFFFF",
        "meta_icon_color": "#CBF44E",
        "card_bg": "#0F1F40",
        "card_border": "#1A2848",
        "card_radius": 28,
    },

    # 段落正文 / 副标题等通用组件的主题覆盖
    "lead_paragraph_defaults": {
        "panel_style": "frosted",
        "text_color": "#FFFFFF",
        "font_size": 28,
    },

    "subtitle_text_defaults": {
        "color_main": "#FFFFFF",
        "color_glow": "#CBF44E",
        "color_stroke": "#CBF44E",
    },

    "section_title_bar_defaults": {
        "accent_color": "#CBF44E",
        "text_color": "#FFFFFF",
    },
}


def get_theme(name: str = "ai_bootcamp"):
    """根据 brief.theme 字段返回主题字典；不认识就返回 None。"""
    if name in ("ai_bootcamp", "ai_bootcamp_navy"):
        return THEME
    return None


def apply_theme_to_brief(brief: dict) -> dict:
    """如果 brief 顶层声明了 theme，把主题默认值合并到 brief.canvas / 各 section。
    用户已显式写的字段不会被覆盖。
    """
    theme_name = brief.get("theme")
    if not theme_name:
        return brief

    theme = get_theme(theme_name)
    if not theme:
        return brief

    # 1. canvas 兜底
    canvas = brief.setdefault("canvas", {})
    for k, v in theme["canvas_defaults"].items():
        canvas.setdefault(k, v)

    # 2. 把主题调色板挂到 brief 上，组件可读
    brief["_theme"] = theme

    return brief
