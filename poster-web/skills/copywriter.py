"""海报文案 skill：基于项目背景 + KB 检索，生成符合 skill md_to_brief 约定的 markdown。

输出双轨：
- output.md：LLM 直接生成的 markdown（人能看、人能改、md_to_brief 能吃）
- output.json：{md, fields}（可选，扩展用，目前只存 md 引用）

特点：
- 流式输出（用户能看到 token 实时打字）
- 严格按 skill 约定输出，让下游海报生成可直接用
"""
import json
from typing import Iterator

from skills.runner import build_kb_context, load_prompt
from skills.strategy_bridge import normalize_generation_params


SCENE_LABEL = {"S1": "招生宣传", "S2": "开营通知", "S3": "课程预告", "S4": "结业总结"}
TONE_LABEL = {
    "auto": "AI 自动判断", "business": "专业稳重", "energetic": "活力激发",
    "warm": "温暖亲和", "tech": "科技前沿", "premium": "高端尊贵",
}


def _build_messages(project: dict, params: dict, kb_module) -> list:
    template = load_prompt("copywriter")
    if not template:
        template = "你是海报文案助手。基于背景生成 markdown。"

    scene = params.get("scene") or "S1"
    tone = params.get("tone") or "auto"
    strategy = params.get("project_strategy") or {}
    strategy_scene = strategy.get("scene") or {}
    strategy_type = strategy.get("project_type") or {}
    module_plan = strategy.get("module_plan") or []
    module_lines = [
        _format_module_line(m)
        for m in module_plan if isinstance(m, dict)
    ]

    # 检索查询：项目名 + 场景 + 调性
    kb_query = f"{project.get('name', '')} {SCENE_LABEL.get(scene, '')} {TONE_LABEL.get(tone, '')}"
    kb_context = build_kb_context(project, kb_query, kb_module, top_k=5)
    if not kb_context:
        kb_context = "（无相关知识库资料，请基于项目名称与描述发挥）"

    extra = (params.get("extra") or "").strip() or "无"

    system_prompt = (template
        .replace("{{PROJECT_NAME}}", project.get("name", "未命名项目"))
        .replace("{{PROJECT_DESC}}", project.get("description", "（暂无简介）"))
        .replace("{{KB_CONTEXT}}", kb_context[:6000])
        .replace("{{SCENE}}", scene)
        .replace("{{SCENE_LABEL}}", strategy_scene.get("label") or SCENE_LABEL.get(scene, scene))
        .replace("{{TONE}}", tone)
        .replace("{{TONE_LABEL}}", strategy_type.get("style_label") or TONE_LABEL.get(tone, tone))
        .replace("{{EXTRA}}", extra)
    )
    system_prompt += (
        "\n\n【新版本项目策略为唯一生成依据】\n"
        f"项目类型：{strategy_type.get('label') or '未指定'}\n"
        f"海报场景：{strategy_scene.get('label') or scene}\n"
        f"说服策略：{strategy_type.get('persuasion_strategy') or '未指定'}\n"
        f"风格策略：{strategy_type.get('style_label') or '未指定'}\n"
        f"逻辑链路：{strategy_scene.get('logic_chain') or '未指定'}\n"
        "必须按以下模块计划生成文案，不得自由增删核心模块：\n"
        + ("\n".join(module_lines) if module_lines else "（暂无模块计划）")
        + "\n\n如果模块里有【用户填写内容】，必须优先使用这些内容；如果有【模块图片】，文案中要为该模块保留图片位置说明，但不要编造图片内容。"
    )

    user_msg = (
        f"现在请按上面规则，为「{project.get('name', '未命名项目')}」"
        f"生成 {strategy_scene.get('label') or SCENE_LABEL.get(scene, scene)} 场景的海报文案。"
        f"\n\n直接输出 markdown，第一行必须是 # 开头的主标题。"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]


def _format_module_line(module: dict) -> str:
    cfg = module.get("module_config") or {}
    title = cfg.get("module_title") or module.get("name") or ""
    content = (cfg.get("content") or "").strip()
    images = cfg.get("images") or []
    parts = [
        f"- {module.get('id')} {module.get('name')}（{'必选' if module.get('required') else '可选'}）",
        f"标题={title}" if cfg.get("title_enabled", True) else "不显示模块标题",
        f"目的={module.get('purpose')}",
        f"script={module.get('script_key')}",
    ]
    if content:
        parts.append(f"用户填写内容：{content[:1000]}")
    if images:
        names = "、".join((img.get("name") or img.get("asset_label") or "图片") for img in images[:6] if isinstance(img, dict))
        parts.append(f"模块图片：{names}")
    return "；".join(parts)


def _validate_md(md: str) -> tuple[bool, str]:
    """简单校验 LLM 输出的 md 是否符合 skill 约定。返回 (ok, reason)。"""
    if not md.strip():
        return False, "输出为空"
    lines = md.strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        return False, "首行不是 # 主标题"
    # 至少包含 1 个 ## 二级标题
    has_h2 = any(l.strip().startswith("## ") for l in lines)
    if not has_h2:
        return False, "没有任何 ## 二级标题"
    return True, ""


def run(project: dict, params: dict, kb_module, llm) -> Iterator[dict]:
    """主入口。"""
    params = normalize_generation_params(params)
    yield {"type": "progress", "data": "正在检索项目知识库…"}

    messages = _build_messages(project, params, kb_module)

    yield {"type": "progress", "data": "AI 文案生成中…"}

    full = ""
    try:
        for ev in llm.chat_stream(messages, temperature=0.5, timeout=180):
            t = ev.get("type")
            if t == "token":
                full += ev.get("data", "")
                yield ev
            elif t == "error":
                yield ev
                return
    except Exception as e:
        yield {"type": "error", "data": f"LLM 调用失败：{e}"}
        return

    if not full.strip():
        yield {"type": "error", "data": "LLM 返回为空"}
        return

    # 清洗：去除可能的 ```markdown 包裹
    md = full.strip()
    if md.startswith("```"):
        # 删除起始 ```xxx 行
        lines = md.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        md = "\n".join(lines).strip()

    # 校验
    ok, reason = _validate_md(md)
    if not ok:
        yield {
            "type": "progress",
            "data": f"⚠️ 输出格式警告：{reason}。仍会保留为 markdown，但下游海报生成可能解析降级。"
        }

    # 把校验后的 markdown 通过 file 事件让 runner 落到 output.md
    # （runner 默认会用 token 累积的 full 落 output.md，但我们要清洗后的）
    yield {"type": "file", "filename": "output.md", "content": md}

    # 也存一份机器读 JSON（暂只存 md 引用 + 元信息，未来扩展 fields）
    json_payload = {
        "md": md,
        "scene": params.get("scene"),
        "tone": params.get("tone"),
        "char_count": len(md),
        "validated": ok,
        "warning": reason if not ok else None,
    }
    yield {"type": "json", "data": json_payload}

    yield {"type": "progress", "data": "✅ 文案生成完成。可直接进入「海报生成」用此文案出图。"}
