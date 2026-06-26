"""海报生成 skill v2：完整接入 skill 自动化能力。

流水线：
1. 找上游 copywriter 产物（output.md，符合 skill md 约定）
   - 没有就让 LLM 现场生成一份 md
2. md_to_brief()：用 skill 内置转换器，把 md 转 brief.json
   - 这一步保留了语义结构，比 LLM 直吐 brief 准确
3. [可选] 自动生成主视觉底图（image API / 用户素材；I4 阶段实施）
4. compose_long_poster()：调 skill 渲染引擎出 PNG
5. 落 artifact：brief.json + content.md + poster.png + cover.jpg

特点：
- brief.json 完整保留，用户可一键进编辑器手动改
- copywriter md 优先复用，保证文案一致
- 渲染失败时清晰报错（不静默降级）
"""
import json
import sys
import time
import pathlib
import traceback
import uuid
from typing import Iterator, Optional

from skills.runner import build_function_kb_context, build_kb_context, load_prompt
from skills.poster_visual_assets import apply_gaming_visual_assets
from skills.strategy_bridge import apply_module_config_to_brief, normalize_generation_params, renderer_palette
from image_client import ImageGenerationError


SCENE_LABEL = {"S1": "招生宣传", "S2": "开营通知", "S3": "课程预告", "S4": "结业总结"}
TONE_LABEL = {
    "auto": "AI 自动判断", "business": "专业稳重", "energetic": "活力激发",
    "warm": "温暖亲和", "tech": "科技前沿", "premium": "高端尊贵",
}

# 调性 → palette 映射（与 skill 的 named:* palette 对齐）
TONE_PALETTE = {
    "business": "named:deep_space",
    "energetic": "named:carnival",
    "warm": "named:festival_red",
    "tech": "named:cyber_neon",
    "premium": "named:velvet_gold",
    "auto": "named:cyber_neon",
}

# 场景默认 palette（覆盖 tone=auto 时用）
SCENE_PALETTE = {
    "S1": "named:cyber_neon",       # 招生宣传：科技感
    "S2": "named:deep_space",       # 开营通知：稳重
    "S3": "named:carnival",         # 课程预告：活力
    "S4": "named:festival_red",     # 结业总结：热烈
}


# ============================================================
# 找上游 copywriter 产物（output.md 符合 skill md 约定）
# ============================================================
def _find_latest_copy_md(project: dict, project_dir: pathlib.Path, function_project_id: str = "") -> Optional[str]:
    """优先找当前海报子项目绑定的 copywriter 产物，再退回项目最新文案。"""
    if function_project_id:
        for item in project.get("function_projects", {}).get("poster_brief", []) or []:
            if item.get("id") == function_project_id and item.get("copy_artifact_id"):
                aid = item.get("copy_artifact_id")
                art = next((a for a in (project.get("artifacts") or []) if a.get("id") == aid), None)
                if art:
                    fp = project_dir / art["path"] / "output.md"
                    if fp.exists():
                        try:
                            return fp.read_text(encoding="utf-8")
                        except Exception:
                            pass
    for art in project.get("artifacts") or []:
        if art.get("skill") == "copywriter":
            fp = project_dir / art["path"] / "output.md"
            if fp.exists():
                try:
                    return fp.read_text(encoding="utf-8")
                except Exception:
                    continue
    return None


# ============================================================
# Prompt：当上游没有文案时，让 LLM 现场生成一份符合约定的 md
# ============================================================
def _build_inline_copy_messages(project: dict, params: dict, kb_module) -> list:
    """没有上游 copywriter 时，复用 copywriter 的 prompt 现场生成 md。"""
    template = load_prompt("copywriter")
    if not template:
        template = "你是海报文案助手。基于背景生成 markdown。"

    scene = params.get("scene") or "S1"
    tone = params.get("tone") or "auto"
    if tone == "auto":
        tone = "business"  # 内联生成时随便选个默认

    kb_query = f"{project.get('name', '')} {SCENE_LABEL.get(scene, '')}"
    kb_context = build_function_kb_context(project, kb_query, kb_module, "poster_brief", "copy", top_k=5)
    if not kb_context:
        kb_context = build_kb_context(project, kb_query, kb_module, top_k=5)
    if not kb_context:
        kb_context = "（无相关知识库资料）"

    extra = (params.get("extra") or "").strip() or "无"
    strategy = params.get("project_strategy") or {}
    strategy_scene = strategy.get("scene") or {}
    strategy_type = strategy.get("project_type") or {}
    module_plan = strategy.get("module_plan") or []
    module_lines = [
        _format_module_line(m)
        for m in module_plan if isinstance(m, dict)
    ]

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
        "\n\n【新版本项目策略与用户模块配置】\n"
        f"项目类型：{strategy_type.get('label') or '未指定'}\n"
        f"海报场景：{strategy_scene.get('label') or SCENE_LABEL.get(scene, scene)}\n"
        f"逻辑链路：{strategy_scene.get('logic_chain') or '未指定'}\n"
        "必须按以下模块顺序生成 markdown，不得自由改写模块结构：\n"
        + ("\n".join(module_lines) if module_lines else "（暂无模块计划）")
        + "\n\n如果模块里有【用户填写内容】，必须优先使用这些内容；如果有【模块图片】，为该模块保留图片位置说明。"
    )

    user_msg = (
        f"现在请直接生成符合上面 markdown 约定的海报文案，"
        f"用于「{project.get('name', '')}」的 {SCENE_LABEL.get(scene, scene)} 场景。"
        f"\n直接输出 markdown，第一行必须是 # 主标题。"
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


# ============================================================
# 解析 md → brief（调 skill 内置 md_to_brief）
# ============================================================
def _md_to_brief(md_text: str, scene: str, palette: str) -> dict:
    """调 skill 内置 md_to_brief 转换器。"""
    WEB_ROOT = pathlib.Path(__file__).resolve().parents[1]
    PACKAGE_ROOT = WEB_ROOT.parent
    SKILL_DIR = PACKAGE_ROOT / "gaming-training-poster"
    SCRIPTS_DIR = SKILL_DIR / "scripts"
    sys.path.insert(0, str(SCRIPTS_DIR))
    from content_md_to_brief import md_to_brief  # type: ignore
    return md_to_brief(md_text, scene=scene, palette=palette)


# ============================================================
# 渲染（调 skill compose_long_poster）
# ============================================================
def _render_brief(brief: dict) -> tuple[bytes, bytes]:
    """compose_long_poster → (poster.png bytes, cover.jpg bytes)"""
    WEB_ROOT = pathlib.Path(__file__).resolve().parents[1]
    PACKAGE_ROOT = WEB_ROOT.parent
    SKILL_DIR = PACKAGE_ROOT / "gaming-training-poster"
    SCRIPTS_DIR = SKILL_DIR / "scripts"
    sys.path.insert(0, str(SCRIPTS_DIR))
    from compose_poster_v2 import compose_long_poster  # type: ignore

    WEB_ROOT = pathlib.Path(__file__).resolve().parent.parent
    tmp_dir = WEB_ROOT / "outputs" / f"_brief_{uuid.uuid4().hex[:8]}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_png = tmp_dir / "poster.png"

    try:
        compose_long_poster(brief, str(out_png))
        if not out_png.exists():
            raise RuntimeError("引擎运行后未产出 PNG")
        png_bytes = out_png.read_bytes()

        # 缩略图
        from PIL import Image
        full = Image.open(out_png)
        target_w = 720
        ratio = target_w / full.width
        thumb = full.resize((target_w, int(full.height * ratio)), Image.LANCZOS)
        from io import BytesIO
        buf = BytesIO()
        thumb.convert("RGB").save(buf, "JPEG", quality=82, optimize=True)
        thumb_bytes = buf.getvalue()

        return png_bytes, thumb_bytes
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ============================================================
# 主入口
# ============================================================
def run(project: dict, params: dict, kb_module, llm) -> Iterator[dict]:
    params = normalize_generation_params(params)
    pid = project.get("id")
    WEB_ROOT = pathlib.Path(__file__).resolve().parent.parent
    project_dir = WEB_ROOT / "projects" / pid

    scene = params.get("scene") or "S1"
    tone = params.get("tone") or "strategy_locked"
    palette = params.get("legacy_renderer_palette") or renderer_palette(params, "named:cyber_neon")

    # ---- 1. 拿 markdown ----
    use_latest = params.get("use_latest_copy", True)
    md_text = None

    if use_latest:
        md_text = _find_latest_copy_md(project, project_dir, params.get("function_project_id") or "")
        if md_text:
            yield {"type": "progress", "data": "✓ 找到当前海报子项目文案产物，将复用"}
        else:
            yield {"type": "progress", "data": "未找到海报文案产物，AI 将先生成一份再出图"}

    if not md_text:
        # 现场生成
        yield {"type": "progress", "data": "AI 文案生成中（内嵌）…"}
        messages = _build_inline_copy_messages(project, params, kb_module)
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
            yield {"type": "error", "data": f"LLM 文案调用失败：{e}"}
            return

        if not full.strip():
            yield {"type": "error", "data": "LLM 返回为空"}
            return

        # 清洗 markdown 包裹
        md_text = full.strip()
        if md_text.startswith("```"):
            lines = md_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            md_text = "\n".join(lines).strip()

    # 校验 md
    if not md_text.lstrip().startswith("# "):
        yield {
            "type": "progress",
            "data": "⚠️ 文案 md 首行不是 #，可能解析降级"
        }

    # ---- 2. md → brief ----
    yield {"type": "progress", "data": "解析 markdown → brief.json…"}
    try:
        brief = _md_to_brief(md_text, scene=scene, palette=palette)
        brief = apply_module_config_to_brief(brief, params)
    except Exception as e:
        yield {
            "type": "error",
            "data": f"md_to_brief 解析失败：{e}",
            "traceback": traceback.format_exc()[:1500],
        }
        return

    # 必要字段兜底
    if "canvas" not in brief:
        brief["canvas"] = {}
    brief["canvas"].setdefault("width", 1440)
    brief["background_decorations"] = None  # 禁用底层装饰，避免素材路径错误

    # ---- 3. gaming-training-poster §13 生图流程：L1 → L2 → L3 ----
    yield {"type": "progress", "data": "正在按 gaming-training-poster skill §13 生成全局底图 L1、头部底图 L2、主标题艺术字 L3…"}
    image_kb_context = build_function_kb_context(
        project,
        f"{project.get('name', '')} 海报 生图 视觉 风格 底图 艺术字 logo 头像",
        kb_module,
        "poster_brief",
        "image",
        top_k=6,
    )
    if image_kb_context:
        params = dict(params)
        prefix = "【海报生图知识库参考】\n" + image_kb_context[:3000]
        params["global_bg_prompt"] = "\n\n".join([prefix, params.get("global_bg_prompt") or ""]).strip()
        params["hero_bg_prompt"] = "\n\n".join([prefix, params.get("hero_bg_prompt") or ""]).strip()
        params["wordart_prompt"] = "\n\n".join([prefix, params.get("wordart_prompt") or ""]).strip()
        yield {"type": "progress", "data": "✓ 已读取海报生图知识库，加入 L1/L2/L3 生图提示词"}

    try:
        brief = apply_gaming_visual_assets(
            brief, project, params,
            progress=lambda msg: None,
        )
    except ImageGenerationError as e:
        yield {"type": "error", "data": str(e)}
        return
    except Exception as e:
        yield {
            "type": "error",
            "data": f"gaming-training-poster 生图流程失败：{e}",
            "traceback": traceback.format_exc()[:1500],
        }
        return

    # 把生图流程进度补发给前端，避免 lambda 内 yield 语义复杂。
    if brief.get("canvas", {}).get("global_bg_path"):
        yield {"type": "progress", "data": "✓ 已生成全局底图 L1、头部底图 L2、主标题艺术字 L3，并写入 brief"}

    # ---- 4. 输出 brief（先吐给前端预览） ----
    yield {"type": "json", "data": brief}

    # ---- 5. 渲染 ----
    yield {"type": "progress", "data": "调用渲染引擎生成海报中…（5-10 秒）"}
    t0 = time.time()
    try:
        png_bytes, thumb_bytes = _render_brief(brief)
    except Exception as e:
        yield {
            "type": "error",
            "data": f"渲染失败：{e}",
            "traceback": traceback.format_exc()[:1500],
        }
        return
    dt = time.time() - t0
    yield {"type": "progress", "data": f"✅ 海报渲染完成，耗时 {dt:.1f}s"}

    # ---- 6. 落盘文件 ----
    yield {"type": "file", "filename": "poster.png", "content": png_bytes}
    yield {"type": "file", "filename": "cover.jpg", "content": thumb_bytes}
    yield {"type": "file", "filename": "content.md", "content": md_text}
    # output.json 由 runner 通过 'json' 事件落盘（就是 brief.json 内容）
