"""上传文案识别成图 skill。

流程：
1. 前端先把 Word/PDF/MD/TXT 上传到项目知识库，拿到 doc_id
2. 本 skill 读取该文档 text.txt
3. DeepSeek 将原文整理成 md_to_brief 可解析的规范 Markdown
4. md_to_brief → compose_long_poster，产出 PNG + cover
"""
import json
import pathlib
import re
import traceback
from typing import Iterator, Optional, Tuple

from kb import KB_DATA_DIR
from kb.loader import load as load_doc
from skills.runner import load_prompt
from skills.poster_brief import _md_to_brief, _render_brief, TONE_PALETTE, SCENE_PALETTE
from skills.poster_visual_assets import apply_gaming_visual_assets
from skills.strategy_bridge import apply_module_config_to_brief, normalize_generation_params, renderer_palette
from image_client import ImageGenerationError


SCENE_LABEL = {"S1": "招生宣传", "S2": "开营通知", "S3": "课程预告", "S4": "结业总结"}
TONE_LABEL = {
    "auto": "AI 自动判断", "business": "专业稳重", "energetic": "活力激发",
    "warm": "温暖亲和", "tech": "科技前沿", "premium": "高端尊贵",
}

MAX_SOURCE_CHARS = 12000


def _read_doc_text(
    doc_id: str,
    project_id: Optional[str],
    scope: Optional[str] = None,
    function_id: Optional[str] = None,
    kb_type: Optional[str] = None,
) -> tuple[str, dict]:
    """读取知识库文档。优先按明确 scope 读取，兼容旧 project/global 文档。"""
    candidates = []
    if scope == "function" and project_id and function_id:
        candidates.append(KB_DATA_DIR / "functions" / project_id / function_id / (kb_type or "general") / doc_id)
    if scope == "project" and project_id:
        candidates.append(KB_DATA_DIR / "projects" / project_id / doc_id)
    if scope == "global":
        candidates.append(KB_DATA_DIR / "global" / doc_id)

    if project_id:
        candidates.append(KB_DATA_DIR / "functions" / project_id / "poster_brief" / "copy" / doc_id)
        candidates.append(KB_DATA_DIR / "projects" / project_id / doc_id)
    candidates.append(KB_DATA_DIR / "global" / doc_id)

    # 兜底：遍历所有项目目录，兼容迁移后的 doc_id
    projects_dir = KB_DATA_DIR / "projects"
    if projects_dir.exists():
        for pdir in projects_dir.iterdir():
            if pdir.is_dir():
                candidates.append(pdir / doc_id)

    for ddir in candidates:
        text_fp = ddir / "text.txt"
        meta_fp = ddir / "meta.json"
        if text_fp.exists():
            meta = {}
            if meta_fp.exists():
                try:
                    meta = json.loads(meta_fp.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            # 兼容旧上传：之前 docx 解析会把所有表格追加到末尾；这里优先按修复后的 loader 重读原文件。
            original = ddir / f"original.{meta.get('format', '')}"
            if original.exists() and meta.get("format") == "docx":
                try:
                    text = load_doc(original).strip()
                    text_fp.write_text(text, encoding="utf-8")
                    return text, meta
                except Exception:
                    pass
            text = text_fp.read_text(encoding="utf-8", errors="replace").strip()
            return text, meta
    raise FileNotFoundError(f"知识库文档不存在或未解析完成：{doc_id}")


def _build_messages(project: dict, params: dict, source_text: str, meta: dict) -> list:
    template = load_prompt("poster_copy_import")
    if not template:
        template = "你是海报文案证据驱动结构识别助手。忠实保留原文，同时积极识别标题、段落、列表、普通表格、复杂表格和讲师等明确结构，第一行必须是 # 主标题。"

    extra = (params.get("extra") or "").strip() or "无"
    filename = meta.get("filename") or params.get("filename") or "上传文档"
    clipped = source_text[:MAX_SOURCE_CHARS]
    if len(source_text) > MAX_SOURCE_CHARS:
        clipped += "\n\n[原文过长，已截取前部内容用于本次识别。]"

    system_prompt = (
        template
        .replace("{{PROJECT_NAME}}", project.get("name", "未命名项目"))
        .replace("{{PROJECT_DESC}}", project.get("description", "（暂无简介）"))
        .replace("{{SOURCE_TEXT}}", f"文档：{filename}\n\n{clipped}")
        .replace("{{EXTRA}}", extra)
    )

    user_msg = (
        f"请仅依据「{filename}」原文做证据驱动的结构识别：忠实保留原文措辞，同时积极识别讲师/嘉宾、普通表格、复杂表格、日程排期等明确结构。"
        f"场景={SCENE_LABEL.get(params.get('scene') or 'S1')}，调性={TONE_LABEL.get(params.get('tone') or 'auto')} 只用于后续视觉排版，不得影响文案内容；不要新增原文不存在的事实。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]


def _clean_markdown(md: str) -> str:
    md = (md or "").strip()
    if md.startswith("```"):
        lines = md.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        md = "\n".join(lines).strip()
    return md



def _cell_text(value) -> str:
    return str(value or "").strip()


def _is_table_row(line: str) -> bool:
    t = line.strip()
    return t.startswith("|") and t.endswith("|")


def _parse_md_table(lines: list) -> Tuple[Optional[dict], int]:
    table_lines = []
    idx = 0
    while idx < len(lines) and _is_table_row(lines[idx]):
        table_lines.append(lines[idx])
        idx += 1
    if not table_lines:
        return None, 0
    rows = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and all(re.match(r"^[-:\s]*$", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return None, idx
    headers = rows[0]
    data_rows = rows[1:]
    return {"headers": headers, "rows": data_rows}, idx


def _trim_empty_table_edges(headers: list, rows: list) -> Tuple[list, list]:
    headers = list(headers or [])
    rows = [list(r) for r in (rows or []) if isinstance(r, list)]
    col_count = max([len(headers)] + [len(r) for r in rows] + [0])
    headers += [""] * (col_count - len(headers))
    rows = [r + [""] * (col_count - len(r)) for r in rows]
    while col_count > 0 and not _cell_text(headers[-1]) and all(not _cell_text(r[-1]) for r in rows):
        headers.pop()
        rows = [r[:-1] for r in rows]
        col_count -= 1
    return headers, rows


def _is_complex_table(headers, rows) -> bool:
    """Only upgrades layout choice; cell text remains exactly from markdown/original."""
    headers = headers or []
    rows = rows or []
    col_count = max([len(headers)] + [len(r) for r in rows if isinstance(r, list)] + [0])
    if col_count >= 4 and len(rows) >= 3:
        return True
    if col_count >= 5:
        return True
    long_cells = 0
    repeated_first_col = False
    seen_first = set()
    for row in rows:
        if not isinstance(row, list):
            continue
        if row:
            first = _cell_text(row[0])
            if first and first in seen_first:
                repeated_first_col = True
            seen_first.add(first)
        for cell in row:
            if len(_cell_text(cell)) >= 28 or "\n" in _cell_text(cell):
                long_cells += 1
    if long_cells >= 3 and col_count >= 3:
        return True
    if repeated_first_col and col_count >= 3 and len(rows) >= 4:
        return True
    return False


def _table_section(table: dict) -> dict:
    headers = table.get("headers") or []
    rows = table.get("rows") or []
    headers, rows = _trim_empty_table_edges(headers, rows)
    if not _is_complex_table(headers, rows):
        return {
            "type": "data_table",
            "headers": headers,
            "rows": rows,
            "style": "soft",
        }
    col_count = max([len(headers)] + [len(r) for r in rows if isinstance(r, list)] + [0])
    complex_rows = []
    for row in rows:
        if not isinstance(row, list):
            continue
        cells = [{"text": _cell_text(cell), "align": "center"} for cell in row]
        if len(cells) < col_count:
            cells.extend({"text": "", "align": "center"} for _ in range(col_count - len(cells)))
        complex_rows.append(cells[:col_count])
    return {
        "type": "complex_table",
        "col_count": col_count,
        "headers": [{"text": _cell_text(h), "align": "center", "bold": True} for h in headers[:col_count]],
        "rows": complex_rows,
        "col_weights": _infer_col_weights(headers, rows, col_count),
        "font_size": 22 if col_count >= 5 else 24,
        "pad": 16,
    }


def _infer_col_weights(headers, rows, col_count: int) -> list:
    weights = []
    for idx in range(col_count):
        samples = []
        if idx < len(headers):
            samples.append(_cell_text(headers[idx]))
        for row in rows:
            if isinstance(row, list) and idx < len(row):
                samples.append(_cell_text(row[idx]))
        avg_len = sum(len(s) for s in samples) / max(1, len(samples))
        if avg_len <= 4:
            weights.append(0.75)
        elif avg_len >= 18:
            weights.append(1.7)
        elif avg_len >= 10:
            weights.append(1.25)
        else:
            weights.append(1.0)
    return weights


def _parse_md_blocks(md_text: str) -> Tuple[str, str, list]:
    title = "主标题"
    subtitle = ""
    blocks = []
    cur_title = None
    cur_lines = []

    def flush():
        nonlocal cur_title, cur_lines
        if cur_title is not None:
            blocks.append({"title": cur_title, "lines": cur_lines[:]})
        cur_title = None
        cur_lines = []

    for raw in md_text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip() or title
        elif stripped.startswith(">") and cur_title is None:
            subtitle = stripped.lstrip(">").strip()
        elif stripped.startswith("## "):
            flush()
            cur_title = stripped[3:].strip()
            cur_lines = []
        else:
            if cur_title is not None:
                cur_lines.append(line)
    flush()
    return title, subtitle, blocks


def _looks_like_people_title(title: str) -> bool:
    return any(k in title for k in ["讲师", "嘉宾", "导师", "顾问", "分享人", "专家", "阵容"])



def _parse_people(lines: list[str]) -> list[dict]:
    members = []
    seen = set()
    name_pat = r"[\w.-]+[（(][\u4e00-\u9fff]{2,4}[）)]|[\u4e00-\u9fff]{2,4}"

    def add(name: str, title: str = "", intro: str = ""):
        name = _cell_text(name)
        title = _cell_text(title)
        intro = _cell_text(intro)
        if not name or name in seen:
            return
        # 避免把普通短中文词误当人名；英文ID+中文括号最可靠。
        if not (re.search(r"[\w.-]+[（(][\u4e00-\u9fff]{2,4}[）)]", name) or re.match(r"^[\u4e00-\u9fff]{2,4}$", name)):
            return
        item = {"name": name}
        if title:
            item["title"] = title
        if intro:
            item["intro"] = intro
        members.append(item)
        seen.add(name)

    clean = [ln.strip() for ln in lines if ln.strip()]
    for raw in clean:
        t = raw[2:].strip() if raw.startswith(('- ', '* ')) else raw
        if "/" not in t:
            continue
        parts = [p.strip() for p in re.split(r"\s*/\s*", t) if p.strip()]
        if parts:
            add(parts[0], parts[1] if len(parts) >= 2 else "", " / ".join(parts[2:]) if len(parts) >= 3 else "")

    # 识别 Word/PDF 抽出的顾问网格：一行多个姓名，下一行多个职务。
    i = 0
    while i < len(clean):
        line = clean[i]
        names = re.findall(r"[\w.-]+[（(][\u4e00-\u9fff]{2,4}[）)]", line)
        if not names:
            i += 1
            continue
        next_line = clean[i + 1] if i + 1 < len(clean) else ""
        next_has_names = bool(re.search(r"[\w.-]+[（(][\u4e00-\u9fff]{2,4}[）)]", next_line))
        if next_line and not next_has_names:
            titles = [p.strip() for p in re.split(r"\s{2,}", next_line) if p.strip()]
            if len(titles) < len(names) and len(names) == 1:
                titles = [next_line.strip()]
            for idx, name in enumerate(names):
                add(name, titles[idx] if idx < len(titles) else "")
            i += 2
        else:
            for name in names:
                add(name)
            i += 1
    return members


def _plain_lines(lines: list[str]) -> list[str]:
    return [ln.strip() for ln in lines if ln.strip() and not re.match(r"^\|\s*[-:]+", ln.strip())]


def _copy_md_to_brief(md_text: str, scene: str, palette: str) -> dict:
    """Poster copy import converter: preserve original block order and choose modules by evidence."""
    base = _md_to_brief(md_text, scene=scene, palette=palette)
    title, subtitle, blocks = _parse_md_blocks(md_text)
    hero = base.get("sections", [{}])[0] if base.get("sections") else {}
    hero.setdefault("type", "hero_strip")
    hero.setdefault("title_card", {})
    hero["title_card"].update({
        "style": hero["title_card"].get("style", "ai_wordart"),
        "lines": [title],
        "subtitle": subtitle,
    })
    sections = [hero]
    section_index = 1

    for block in blocks:
        block_title = block.get("title") or ""
        raw_lines = block.get("lines") or []
        lines = _plain_lines(raw_lines)
        if not lines:
            continue

        sections.append({
            "type": "section_title_bar",
            "style": "plain",
            "text": block_title,
            "text_color": "#FFFFFF",
            "underline_color": "auto",
        })
        section_index += 1

        people = _parse_people(lines) if _looks_like_people_title(block_title) else []
        if people:
            sections.append({
                "type": "faculty_grid",
                "layout": "grid" if len(people) >= 5 else ("compact" if len(people) > 2 else "detail"),
                "cols": 5 if len(people) >= 5 else min(3, max(1, len(people))),
                "members": people,
            })
            continue

        consumed_any = False
        i = 0
        pending_text = []
        while i < len(lines):
            table, consumed = _parse_md_table(lines[i:])
            if table:
                if pending_text:
                    sections.append(_text_section(block_title, pending_text))
                    pending_text = []
                sections.append(_table_section(table))
                consumed_any = True
                i += consumed
            else:
                pending_text.append(lines[i])
                i += 1
        if pending_text:
            sections.append(_text_section(block_title, pending_text))
        elif not consumed_any:
            sections.append(_text_section(block_title, lines))

    base["sections"] = sections
    return base


def _text_section(title: str, lines: list[str]) -> dict:
    bullet_lines = [ln[2:].strip() for ln in lines if ln.strip().startswith(('- ', '* '))]
    if bullet_lines and len(bullet_lines) == len(lines):
        return {"type": "bullet_points_block", "bullets": bullet_lines}
    text = "\n".join(lines).strip()
    if any(k in title for k in ["须知", "注意", "规则", "要求"]):
        paras = [p.strip('- ').strip() for p in lines if p.strip()]
        return {"type": "notice_box", "inline": True, "bullets": paras or [text]}
    return {"type": "lead_paragraph", "panel_style": "frosted", "text": text}

def run(project: dict, params: dict, kb_module, llm) -> Iterator[dict]:
    params = normalize_generation_params(params)
    doc_id = (params.get("doc_id") or "").strip()
    if not doc_id:
        yield {"type": "error", "data": "缺少 doc_id：请先上传一份文案文档"}
        return

    scene = params.get("scene") or "S1"
    tone = params.get("tone") or "strategy_locked"
    palette = params.get("legacy_renderer_palette") or renderer_palette(params, "named:cyber_neon")

    yield {"type": "progress", "data": "正在读取项目知识库文档…"}
    try:
        source_text, meta = _read_doc_text(
            doc_id,
            project.get("id"),
            scope=params.get("doc_scope"),
            function_id=params.get("function_id"),
            kb_type=params.get("kb_type"),
        )
    except Exception as e:
        yield {"type": "error", "data": str(e)}
        return

    if not source_text.strip():
        yield {"type": "error", "data": "文档解析文本为空，请换一份非扫描版文档"}
        return

    yield {"type": "progress", "data": "AI 正在识别原文标题、讲师、普通表格与复杂表格结构…"}
    messages = _build_messages(project, params, source_text, meta)

    full = ""
    try:
        for ev in llm.chat_stream(messages, temperature=0.0, timeout=180):
            if ev.get("type") == "token":
                full += ev.get("data", "")
                yield ev
            elif ev.get("type") == "error":
                yield ev
                return
    except Exception as e:
        yield {"type": "error", "data": f"LLM 文案识别失败：{e}"}
        return

    md_text = _clean_markdown(full)
    if not md_text:
        yield {"type": "error", "data": "AI 返回为空"}
        return
    if not md_text.lstrip().startswith("# "):
        yield {"type": "progress", "data": "⚠️ 识别结果首行不是 # 主标题，后续解析可能降级"}

    yield {"type": "file", "filename": "output.md", "content": md_text}
    yield {"type": "file", "filename": "content.md", "content": md_text}
    yield {
        "type": "file",
        "filename": "source.json",
        "content": json.dumps({
            "doc_id": doc_id,
            "filename": meta.get("filename"),
            "scene": scene,
            "tone": tone,
            "extra": params.get("extra") or "",
            "source_char_count": len(source_text),
        }, ensure_ascii=False, indent=2),
    }

    yield {"type": "progress", "data": "正在转换 Markdown → brief.json…"}
    try:
        brief = _copy_md_to_brief(md_text, scene=scene, palette=palette)
        brief = apply_module_config_to_brief(brief, params)
    except Exception as e:
        yield {
            "type": "error",
            "data": f"md_to_brief 解析失败：{e}",
            "traceback": traceback.format_exc()[:1500],
        }
        return

    brief.setdefault("canvas", {})
    brief["canvas"].setdefault("width", 1440)
    brief["background_decorations"] = None

    yield {"type": "progress", "data": "正在按 gaming-training-poster skill §13 生成全局底图 L1、头部底图 L2、主标题艺术字 L3…"}
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
    if brief.get("canvas", {}).get("global_bg_path"):
        yield {"type": "progress", "data": "✓ 已生成并写入 L1/L2/L3 视觉素材"}

    yield {"type": "json", "data": brief}

    yield {"type": "progress", "data": "调用渲染引擎生成海报中…"}
    try:
        png_bytes, thumb_bytes = _render_brief(brief)
    except Exception as e:
        yield {
            "type": "error",
            "data": f"渲染失败：{e}",
            "traceback": traceback.format_exc()[:1500],
        }
        return

    yield {"type": "file", "filename": "poster.png", "content": png_bytes}
    yield {"type": "file", "filename": "cover.jpg", "content": thumb_bytes}
    yield {"type": "progress", "data": "✅ 已根据上传文案生成海报，可进入编辑器继续调整。"}
