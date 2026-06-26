"""Skill 注册表：海报系列 2 个能力。

【加新 skill 流程】
1. 写 skills/<name>.py（实现 run(project, params, kb, llm)）
2. 写 prompts/<name>.txt
3. 在下面 SKILLS dict 加一项
"""
from typing import Dict


POSTER_SCENES = [
    {"value": "S1", "label": "招生宣传"},
    {"value": "S2", "label": "开营通知"},
    {"value": "S3", "label": "课程预告"},
    {"value": "S4", "label": "结业总结"},
]

POSTER_TONES = [
    {"value": "auto", "label": "AI 自动判断"},
    {"value": "business", "label": "专业稳重"},
    {"value": "energetic", "label": "活力激发"},
    {"value": "warm", "label": "温暖亲和"},
    {"value": "tech", "label": "科技前沿"},
    {"value": "premium", "label": "高端尊贵"},
]


SKILLS: Dict[str, dict] = {
    # ============================================================
    # 海报文案：基于项目背景 + KB → 结构化板块文案
    # ============================================================
    "copywriter": {
        "label": "海报文案",
        "icon": "✍️",
        "sub": "结合项目背景自动生成各板块文案",
        "category": "poster",
        "form": [
            {
                "key": "extra",
                "label": "补充要求（可选）",
                "type": "textarea",
                "placeholder": "如：标题不超过 12 字 / 强调时间紧迫感 / 突出某讲师",
            },
        ],
        "output": "json",
        "follow_up": {"action": "apply_to_editor", "label": "一键填回编辑器"},
    },

    # ============================================================
    # 海报生成：基于上游文案 + 项目背景 → AI 直接出 brief 并渲染 PNG
    # ============================================================
    "poster_brief": {
        "label": "海报生成",
        "icon": "🎨",
        "sub": "基于文案与项目背景，AI 自动生成完整海报",
        "category": "poster",
        "form": [
            {
                "key": "use_latest_copy",
                "label": "复用最新文案产物（如有）",
                "type": "bool",
                "default": True,
                "help": "若已生成过文案，会自动套用；否则 AI 会先在内部生成一份再渲染",
            },
            {
                "key": "extra",
                "label": "补充要求（可选）",
                "type": "textarea",
                "placeholder": "如：用深蓝商务风 / 突出时间地点",
            },
            {
                "key": "generate_visual_assets",
                "label": "按 gaming poster skill 自动生成全局底图/头部底图/艺术字",
                "type": "bool",
                "default": True,
                "help": "开启后会调用生图模型生成 L1/L2/L3，并写入 brief 后再渲染",
            },
        ],
        "output": "json",
        "follow_up": {"action": "open_editor", "label": "进入编辑器调整"},
    },

    # ============================================================
    # 上传文案识别成图：Word/PDF/MD/TXT → 规范 markdown → brief → PNG
    # ============================================================
    "poster_copy_import": {
        "label": "上传文案识别成图",
        "icon": "📄",
        "sub": "上传已有海报文案，自动识别结构并生成海报",
        "category": "poster",
        "form": [
            {"key": "doc_id", "label": "知识库文档 ID", "type": "text", "required": True},
            {
                "key": "extra",
                "label": "补充要求（可选）",
                "type": "textarea",
                "placeholder": "如：标题更短 / 强调报名截止 / 保留原文活动信息",
            },
            {
                "key": "global_bg_prompt",
                "label": "全局底图要求",
                "type": "textarea",
                "placeholder": "描述整张海报底层背景：主题色渐变、几何装饰、纹理、留白等",
            },
            {
                "key": "hero_bg_prompt",
                "label": "头部底图要求",
                "type": "textarea",
                "placeholder": "描述头部主视觉：构图、光效、中心留空、元素风格等",
            },
            {
                "key": "wordart_prompt",
                "label": "主标题艺术字要求",
                "type": "textarea",
                "placeholder": "描述标题艺术字：颜色、描边、立体感、风格等",
            },
            {
                "key": "generate_visual_assets",
                "label": "按 gaming poster skill 自动生成全局底图/头部底图/艺术字",
                "type": "bool",
                "default": True,
                "help": "开启后上传文案识别成 brief 后，会继续生成 L1/L2/L3 视觉素材",
            },
        ],
        "output": "json",
        "follow_up": {"action": "open_editor", "label": "进入编辑器调整"},
    },
}


def list_skills() -> dict:
    return {"skills": SKILLS}


def get_skill(name: str):
    return SKILLS.get(name)
