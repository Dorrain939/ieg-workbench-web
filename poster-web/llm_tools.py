"""LLM 工具函数定义（OpenAI 风格的 function schema）。

设计原则：
1. 函数粒度 = 用户的一句指令通常对应 1-3 个函数调用
2. 不让 LLM 直接吐 brief JSON（容易错），而是吐"操作指令"
3. 操作指令在前端按顺序执行，每步都可见、可撤销

用法：
    from llm_tools import TOOLS, SYSTEM_PROMPT, build_user_context
    payload = {
        "model": "qwen2.5:14b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_context(brief, user_msg)},
        ],
        "tools": TOOLS,
        "stream": False,
    }
"""

# 命名配色清单（前端可选，LLM 也用这个映射）
PALETTE_NAMES = {
    "霓虹赛博紫": "named:cyber_neon",
    "深空藏蓝": "named:deep_space",
    "极光蓝紫": "named:aurora",
    "嘉年华糖果色": "named:carnival",
    "朱红暖金": "named:festival_red",
    "丝绒金": "named:velvet_gold",
    "电竞竞技场": "named:arena",
    "电路火焰": "named:circuit_flame",
    "引擎核心荧光绿": "named:engine_core",
    "炭黑勋章金": "named:charcoal_gold",
    "夕阳街机": "named:sunset_arcade",
    "水墨荣耀": "named:ink_honor",
    "像素暖晨光": "named:pixel_dawn",
    "星云蓝": "named:nebula_blue",
}

# 所有 section 类型（LLM 看到的中文别名 + 真名）
SECTION_TYPE_HINTS = {
    "顶部 Logo 横幅": "top_logo_bar",
    "主标题艺术字": "hero_strip",
    "副标题": "subtitle_text",
    "模块标题": "section_title_bar",
    "段落正文": "lead_paragraph",
    "要点块": "bullet_points_block",
    "图片块": "image_block",
    "数据表格": "data_table",
    "讲师团": "faculty_grid",
    "顾问团": "faculty_grid",
    "复杂表格": "complex_table",
    "注意事项": "notice_box",
    "学员须知": "notice_box",
    "联系方式": "contact_inline",
    "信息卡": "info_card",
    "CTA 按钮": "cta_button",
}

# OpenAI 风格的 tools 定义
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "set_palette",
            "description": "切换整张海报的配色方案。用户说'改成紫色/蓝色/朱红色配色'时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "palette": {
                        "type": "string",
                        "description": (
                            "配色方案名。可选："
                            "named:cyber_neon（霓虹赛博紫）, "
                            "named:deep_space（深空藏蓝）, "
                            "named:aurora（极光蓝紫）, "
                            "named:carnival（嘉年华糖果色）, "
                            "named:festival_red（朱红暖金）, "
                            "named:velvet_gold（丝绒金）, "
                            "named:arena（电竞）, "
                            "named:engine_core（引擎核心荧光绿）, "
                            "named:charcoal_gold（炭黑勋章金）"
                        ),
                    }
                },
                "required": ["palette"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_field",
            "description": (
                "修改某个模块的字段值。用于'把 XX 改成 YY'类指令。"
                "section_index 从 0 开始；field_path 支持点号嵌套，如 'title_card.image' 'text' 'font_size' 'text_color'。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "section_index": {"type": "integer", "description": "section 下标，0 起"},
                    "field_path": {"type": "string", "description": "字段路径，如 text、font_size、title_card.image"},
                    "value": {"description": "新值。字符串/数字/布尔/数组都可"},
                },
                "required": ["section_index", "field_path", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_canvas_field",
            "description": "修改 canvas 全局字段（配色、底图、底色、底纹、底层装饰开关等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_path": {"type": "string", "description": "如 palette_strategy / bg_colors / pattern / glow / bg_image_path"},
                    "value": {"description": "新值"},
                },
                "required": ["field_path", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_section",
            "description": (
                "在指定位置插入新的模块。"
                "section_type 可选值：top_logo_bar / hero_strip / subtitle_text / section_title_bar / lead_paragraph / "
                "bullet_points_block / image_block / data_table / complex_table / faculty_grid / notice_box / contact_inline / info_card / cta_button。"
                "position 是插入后的下标（0 为最前，省略则在末尾）。initial_fields 是这个 section 的初始字段。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "section_type": {"type": "string"},
                    "position": {"type": "integer", "description": "可选，省略则添加到末尾"},
                    "initial_fields": {"type": "object", "description": "可选的初始字段值"},
                },
                "required": ["section_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_section",
            "description": "删除某个 section。",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_index": {"type": "integer"},
                },
                "required": ["section_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_section",
            "description": "移动 section 顺序。把第 from 个移到第 to 个位置。",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_index": {"type": "integer"},
                    "to_index": {"type": "integer"},
                },
                "required": ["from_index", "to_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "duplicate_section",
            "description": "复制某个 section（紧跟在原 section 后面）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_index": {"type": "integer"},
                },
                "required": ["section_index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_notice_highlight",
            "description": "把注意事项（notice_box）中的某条 bullet 标红/取消标红。",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_index": {"type": "integer"},
                    "bullet_index": {"type": "integer"},
                    "highlight": {"type": "boolean"},
                    "color": {"type": "string", "description": "可选，标红色值，默认 #FF4444"},
                },
                "required": ["section_index", "bullet_index", "highlight"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load_template",
            "description": "载入一个内置模板覆盖当前 brief。仅在用户明确说'从 XXX 模板开始'/'套用 XXX' 时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "template_name": {
                        "type": "string",
                        "description": (
                            "模板文件名（不含 brief_ 前缀）。"
                            "常见：vfx-bootcamp-2026, vfx-ue-2026, tech-summit-2026, "
                            "carnival_2026, lunar_new_year_demo"
                        ),
                    }
                },
                "required": ["template_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "answer",
            "description": (
                "当用户只是问问题、或需要解释/确认信息时调用。"
                "不修改 brief，只把回答文本通过这个函数返回。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "回答文本（中文）"},
                },
                "required": ["text"],
            },
        },
    },
]


SYSTEM_PROMPT = """你是腾讯游戏 IEG 海报拼搭器的智能助手。用户用中文跟你描述他想怎么改海报，你必须通过调用工具函数来完成。

【你的职责】
1. 理解用户意图（改配色/加模块/改文字/调字号/排序等）。
2. 决定调用哪些工具函数。一次回答可以调多个函数（按顺序执行）。
3. 如果用户问的是"现在海报里有什么"等查询型问题，调 answer 函数返回文本即可。
4. 严格使用工具函数，不要直接输出修改后的 brief JSON。

【⚠️ 严格守则（违反就是错）】
- 只改用户明确提到的东西。用户说"改配色"就只调 set_palette，不要顺手改 scene、不要删 sections、不要重写整个 brief。
- 用户没要求做的事，绝对不做。
- 不确定时，调 answer 函数把你想做的事描述给用户，让他确认。
- bg_colors 字段是 [深色, 浅色] 两个色值的数组，绝对不能写成单个字符串。优先用 set_palette 切换配色，不要直接改 bg_colors。
- section_index 必须真实存在。当前 sections 在用户消息里有列表，下标范围 0 到 len-1。

【关键规则】
- section_index 从 0 开始计数。当前 brief 的 sections 已在用户消息里以"[索引] 类型 - 摘要"形式列出。
- 涉及"主标题/副标题/段落/讲师团/学员须知/联系方式"等，先看清当前 brief 里哪个 section 对应再操作。
- 用户说"改字号"时：subtitle_text/section_title_bar 的字号字段叫 font_size；lead_paragraph、notice_box、contact_inline、data_table、complex_table 也都有 font_size。
- 用户说"加粗/换字体"时，优先 set_field 改 font_role：display=标题粗体 W7，body=正文体 W3。
- 颜色字段一律用 #RRGGBB 格式；模块标题下划线字段叫 underline_color，正文颜色通常叫 text_color。
- 改"配色方案"调 set_palette；改单个文字颜色调 set_field 改 text_color；改模块标题下划线颜色调 set_field 改 underline_color。
- 如果用户消息里出现“[用户已上传图片，必须按素材类型使用，不能一律当普通配图]”以及图片路径，先读取每张图片的“类型=...”，按类型决定写入位置：
  · 全局底图 → set_canvas_field global_bg_path；头部底图 → set_canvas_field bg_image_path；主标题艺术字图 → 找 hero_strip 后 set_field title_card.image；
  · 联系人二维码 → 找 contact_inline 后 set_field qr_image；人员头像图 → 找 faculty_grid 的对应成员头像，无法匹配时先 answer 询问；
  · 模块素材框 → 写入相关模块 asset_frame_path；模块内容图 → add_section image_block 并把 initial_fields.image_path 设置为该路径。
- 如果旧消息只出现“[用户已上传图片，可用于 image_block]”，才按普通 image_block 处理。
- 用户说"加红加粗某条注意事项"用 set_notice_highlight。

【常见映射】
- "改成紫色风格" → set_palette({"palette": "named:cyber_neon"})  ← 只调这一个，不要再改别的
- "改成深空蓝/商务风" → set_palette({"palette": "named:deep_space"})  ← 同上
- "把第 3 个模块的字号改成 32" → set_field({"section_index": 2, "field_path": "font_size", "value": 32})
- "把副标题改成'欢迎来到 UE 训练营'" → 找到 subtitle_text 的索引 i，set_field({"section_index": i, "field_path": "text", "value": "欢迎来到 UE 训练营"})
- "在合作讲师后面加一个赞助商列表" → add_section({"section_type": "faculty_grid", "position": <合作讲师 idx + 1>})
- "把上传的图放到课程安排前面" → add_section({"section_type":"image_block","position":<课程安排标题 idx>,"initial_fields":{"image_path":"<上传图片路径>","width_ratio":1,"align":"center"}})
- "让学员须知第二条标红" → set_notice_highlight({"section_index": <学员须知 idx>, "bullet_index": 1, "highlight": true})
- "现在有几个模块" → answer({"text": "..."})
"""


def build_user_context(brief: dict, user_msg: str) -> str:
    """把当前 brief 摘要 + 用户消息组装成 LLM 输入。"""
    sections = brief.get("sections", [])
    canvas = brief.get("canvas", {})

    # 摘要每个 section
    lines = []
    for i, s in enumerate(sections):
        t = s.get("type", "?")
        cn = {
            "top_logo_bar": "顶部Logo横幅",
            "hero_strip": "主标题艺术字",
            "subtitle_text": "副标题",
            "section_title_bar": "模块标题",
            "lead_paragraph": "段落正文",
            "bullet_points_block": "要点块",
            "image_block": "图片块",
            "data_table": "数据表格",
            "complex_table": "复杂表格",
            "faculty_grid": "讲师团/顾问团",
            "notice_box": "注意事项",
            "contact_inline": "联系方式",
            "info_card": "信息卡",
            "cta_button": "CTA按钮",
        }.get(t, t)
        # 摘要内容
        summary = ""
        if t == "section_title_bar":
            summary = s.get("text", "")
        elif t == "subtitle_text":
            summary = s.get("text", "")
        elif t == "lead_paragraph":
            summary = (s.get("text", "") or "")[:30]
        elif t == "notice_box":
            bullets = s.get("bullets", [])
            summary = f"{len(bullets)} 条"
        elif t == "bullet_points_block":
            bullets = s.get("bullets", [])
            summary = f"{len(bullets)} 条"
        elif t == "data_table":
            summary = "/".join(s.get("headers", []))
        elif t == "complex_table":
            summary = "/".join([h.get("text", str(h)) if isinstance(h, dict) else str(h) for h in s.get("headers", [])])
        elif t == "faculty_grid":
            summary = f"{len(s.get('members', []))} 人"
        elif t == "contact_inline":
            summary = (s.get("text", "") or "")[:30]
        elif t == "image_block":
            summary = (s.get("image_path", "") or "").split("/")[-1]
        elif t == "info_card":
            summary = (s.get("body", "") or "")[:30]
        lines.append(f"  [{i}] {cn} ({t}) - {summary}")

    sections_summary = "\n".join(lines) if lines else "  （空，还没有 section）"
    palette = canvas.get("palette_strategy", "（未设置）")

    return f"""[当前海报状态]
配色：{palette}
sections（共 {len(sections)} 个）：
{sections_summary}

[用户的指令]
{user_msg}

请调用合适的工具函数完成。"""
