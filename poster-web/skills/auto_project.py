"""auto_project：从知识库文档抽取项目信息，预填新建项目表单。

输入：doc_ids（一个或多个文档 id），可选 user_hint
输出：JSON {name, description, owner_hint, status, cover_id_hint, tags, source_doc_ids}

策略：
- 拼接所有文档前 N 字符（控制 token）作为上下文
- LLM 用 JSON mode 输出（DeepSeek 支持 response_format={"type":"json_object"}）
- 兜底：解析失败时给空草案，前端能感知到

封面推荐：根据文档关键词匹配 8 张预制封面的色调/主题
- "管理/经理/商务/M1/M2" → blue_business
- "实习/onboarding/校招/新员工" → orange_intern
- "安全/隐私/合规/数据" → dark_security 或 pink_security
- "复盘/HRBP/总结" → purple_review
- "领导力/共创" → cyan_leadership
- "技术/分享/工程" → tech_dark
"""
import json
import pathlib
from typing import List, Dict, Optional

from kb import KB_DATA_DIR


# 摘要字符上限：避免 prompt 太大
MAX_DOC_CHARS = 3000
MAX_TOTAL_CHARS = 8000

# 封面 ID 列表（必须和 projects_api.COVER_LIBRARY 对齐）
VALID_COVER_IDS = [
    "blue_business", "orange_intern", "dark_security", "purple_review",
    "cyan_leadership", "teal_campus", "pink_security", "tech_dark",
]


def _read_doc_text(doc_id: str) -> Optional[Dict]:
    """从 kb_data 找文档（先全局再项目目录），返回 {filename, text}"""
    # 全局
    gdir = KB_DATA_DIR / "global" / doc_id
    if gdir.exists():
        return _read_doc_dir(gdir)
    # 项目目录
    pdir = KB_DATA_DIR / "projects"
    if pdir.exists():
        for proj in pdir.iterdir():
            target = proj / doc_id
            if target.exists():
                return _read_doc_dir(target)
    return None


def _read_doc_dir(d: pathlib.Path) -> Optional[Dict]:
    meta_fp = d / "meta.json"
    text_fp = d / "text.txt"
    if not (meta_fp.exists() and text_fp.exists()):
        return None
    try:
        meta = json.loads(meta_fp.read_text(encoding="utf-8"))
        text = text_fp.read_text(encoding="utf-8")
        return {"id": meta["id"], "filename": meta.get("filename", ""), "text": text}
    except Exception:
        return None


def _build_context(doc_ids: List[str]) -> str:
    """把多个文档拼成 prompt 上下文（每篇截取前 MAX_DOC_CHARS）。"""
    parts = []
    total = 0
    for did in doc_ids:
        doc = _read_doc_text(did)
        if not doc:
            continue
        snippet = doc["text"][:MAX_DOC_CHARS]
        block = f"=== 文档：{doc['filename']} ({doc['id']}) ===\n{snippet}\n"
        if total + len(block) > MAX_TOTAL_CHARS:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


SYSTEM_PROMPT = """你是腾讯 IEG 培训海报项目助手。用户上传了若干份培训资料，你需要从中抽取关键信息，生成一份"项目档案"，预填到新建项目表单。

请严格按下面 JSON 格式返回（不要 Markdown 包裹，不要解释）：

{
  "name": "项目名（10-20 字，简洁有力，如「2026 新经理训练营海报」）",
  "description": "一句话简介（30-60 字，说明项目背景与目标受众）",
  "owner_hint": "如果文档里提到具体负责人/对接人姓名，写这里；没有就空字符串",
  "status": "in_progress | pending（默认 in_progress；若文档明确说还在筹备阶段则 pending）",
  "cover_id_hint": "封面 ID，从下面 8 个里选最匹配的：blue_business（深蓝商务，管理/经理/M1/M2 题材）、orange_intern（暖橙，实习/校招/新员工）、dark_security（暗蓝，安全/隐私/合规）、purple_review（深紫，复盘/HRBP/总结）、cyan_leadership（晴蓝，领导力/共创/工作坊）、teal_campus（青翠，校园/学习营）、pink_security（粉调，温暖话题）、tech_dark（暗夜科技，技术/工程分享）",
  "tags": ["关键词1", "关键词2", ...]   // 3-6 个文档主题词
}

【硬规则】
- 只允许输出 JSON 对象，第一个字符必须是 {
- 不准虚构原文中没有的信息（如不准编造时间、地点、人数）
- 文档信息不全也要给出能用的 name 和 description，缺字段写 ""
- cover_id_hint 必须是上面 8 个 id 之一，不要写其他值"""


def extract(doc_ids: List[str], llm) -> Dict:
    """从指定文档抽取项目信息。
    
    参数：
        doc_ids: 文档 ID 列表
        llm: LLMClient 实例
    返回：
        {ok, draft: {...}, source_doc_ids, raw_text?, error?}
    """
    if not doc_ids:
        return {"ok": False, "error": "没有提供文档", "draft": _empty_draft()}

    context = _build_context(doc_ids)
    if not context.strip():
        return {"ok": False, "error": "文档读取失败或为空", "draft": _empty_draft()}

    user_msg = f"""【参考资料】
{context}

【任务】
从上述资料中抽取信息，生成新建项目表单 JSON。"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    try:
        # DeepSeek 支持 response_format=json_object
        result = llm.chat(
            messages=messages,
            temperature=0.2,
            timeout=60,
        )
    except Exception as e:
        return {"ok": False, "error": f"LLM 调用失败：{e}", "draft": _empty_draft()}

    raw = (result.get("content") or "").strip()
    # 容错解析：找第一个 { 到最后一个 }
    try:
        start = raw.index("{")
        end = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])
    except Exception:
        return {
            "ok": False,
            "error": f"LLM 返回无法解析为 JSON：{raw[:200]}",
            "draft": _empty_draft(),
            "raw_text": raw[:500],
        }

    # 校验/清洗字段
    draft = _clean_draft(parsed)
    return {
        "ok": True,
        "draft": draft,
        "source_doc_ids": doc_ids,
        "raw_text": raw[:500],
    }


def _empty_draft() -> Dict:
    return {
        "name": "",
        "description": "",
        "owner_hint": "",
        "status": "in_progress",
        "cover_id_hint": "blue_business",
        "tags": [],
    }


def _clean_draft(parsed: dict) -> Dict:
    name = (parsed.get("name") or "").strip()[:60]
    description = (parsed.get("description") or "").strip()[:200]
    owner_hint = (parsed.get("owner_hint") or "").strip()[:30]
    status = parsed.get("status") or "in_progress"
    if status not in ("in_progress", "pending", "archived"):
        status = "in_progress"
    cover_id_hint = parsed.get("cover_id_hint") or "blue_business"
    if cover_id_hint not in VALID_COVER_IDS:
        cover_id_hint = "blue_business"
    tags = parsed.get("tags") or []
    if isinstance(tags, list):
        tags = [str(t).strip()[:20] for t in tags if t and str(t).strip()][:8]
    else:
        tags = []
    return {
        "name": name,
        "description": description,
        "owner_hint": owner_hint,
        "status": status,
        "cover_id_hint": cover_id_hint,
        "tags": tags,
    }
