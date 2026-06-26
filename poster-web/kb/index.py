"""统一检索接口：search(query, scope, project_id, top_k) -> list[{doc_id, chunk_id, text, score, filename}]

引擎选择：
- BM25（默认）：本地、无依赖（除 jieba+rank_bm25）、中文分词
- Embedding（G6 才接）：OpenAI 兼容 API 算余弦相似度

为了响应快（每次搜索几十毫秒级），采用：
- 简单内存缓存：按 (scope, project_id, function_id, kb_type) 缓存 BM25 模型 + chunk 索引
- 文档增删时主动 invalidate
"""
import json
import threading
from typing import Optional, List, Dict

import jieba
from rank_bm25 import BM25Okapi

from kb import KB_DATA_DIR


# ============================================================
# Tokenize：中文用 jieba，英文/数字保留
# ============================================================
def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    # jieba 切词，过滤纯空白
    tokens = [t.strip().lower() for t in jieba.lcut(text) if t.strip()]
    # 过滤太短的（除非全是英文/数字）
    return [t for t in tokens if len(t) >= 1]


# ============================================================
# 内存索引：把所有 chunk 加载并建 BM25
# ============================================================
class _Index:
    """单一 scope 的索引（memory）。"""

    def __init__(self):
        self.chunks: List[Dict] = []  # [{doc_id, chunk_id, text, filename}, ...]
        self.bm25: Optional[BM25Okapi] = None

    def build(self, chunks: List[Dict]) -> None:
        self.chunks = chunks
        if not chunks:
            self.bm25 = None
            return
        tokenized = [_tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if not self.bm25 or not self.chunks:
            return []
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        scores = self.bm25.get_scores(q_tokens)

        # BM25 在小语料（< 3 文档）上 IDF 可能为 0 或负，导致分数全 0。
        # 兜底：用 token 命中数 + TF 计算一个正分。
        if max(scores) <= 0:
            scores = []
            q_set = set(q_tokens)
            for c in self.chunks:
                tokens = _tokenize(c["text"])
                tok_set = set(tokens)
                hits = q_set & tok_set
                if not hits:
                    scores.append(0.0)
                    continue
                # 命中 token 数 + 出现频次（log 平滑）
                tf = sum(tokens.count(t) for t in hits)
                hit_rate = len(hits) / len(q_set)
                scores.append(hit_rate * 2.0 + tf * 0.05)

        idxed = list(enumerate(scores))
        idxed.sort(key=lambda x: x[1], reverse=True)
        results = []
        for i, sc in idxed[:top_k]:
            if sc <= 0:
                continue
            c = self.chunks[i]
            results.append({**c, "score": float(sc)})
        return results


_lock = threading.Lock()
_cache: Dict[str, _Index] = {}  # cache key -> _Index


def _cache_key(
    scope: str,
    project_id: Optional[str],
    function_id: Optional[str] = None,
    kb_type: Optional[str] = None,
) -> str:
    if scope == "global":
        return "global"
    if scope == "function":
        return f"function::{project_id}::{function_id}::{kb_type or 'general'}"
    return f"project::{project_id}"


def _gather_chunks(
    scope: str,
    project_id: Optional[str],
    function_id: Optional[str] = None,
    kb_type: Optional[str] = None,
) -> List[Dict]:
    """从磁盘把指定 scope 的所有 chunk 加载成一个扁平列表。

    scope=global：仅扫 kb_data/global/
    scope=project + project_id：扫 kb_data/projects/<pid>/ 并合并 kb_data/global/ 中 tag 含 pid 的文档
    scope=function + project_id + function_id + kb_type：仅扫指定功能知识库，不混入项目/全局
    """
    out = []

    def _scan_dir(base: pathlib.Path, tag_filter: Optional[str] = None):
        if not base.exists():
            return
        for ddir in base.iterdir():
            if not ddir.is_dir() or not ddir.name.startswith("doc_"):
                continue
            meta_fp = ddir / "meta.json"
            chunks_fp = ddir / "chunks.json"
            if not (meta_fp.exists() and chunks_fp.exists()):
                continue
            try:
                meta = json.loads(meta_fp.read_text(encoding="utf-8"))
                if meta.get("status") != "ready":
                    continue
                # tag 过滤
                if tag_filter and tag_filter not in (meta.get("tags") or []):
                    continue
                chunks = json.loads(chunks_fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            for c in chunks:
                out.append({
                    "doc_id": meta["id"],
                    "filename": meta.get("filename", ""),
                    "scope": meta.get("scope", "global"),
                    "project_id": meta.get("project_id"),
                    "function_id": meta.get("function_id"),
                    "kb_type": meta.get("kb_type"),
                    "tags": meta.get("tags") or [],
                    "chunk_id": c.get("id"),
                    "text": c.get("text", ""),
                })

    if scope == "global":
        _scan_dir(KB_DATA_DIR / "global")
    elif scope == "project":
        if not project_id:
            return []
        # 1. 项目独占文档（kb_data/projects/<pid>/）
        _scan_dir(KB_DATA_DIR / "projects" / project_id)
        # 2. 全局文档但 tag 含 pid（用户在「新建项目」时上传，scope=global 但 tag=pid）
        _scan_dir(KB_DATA_DIR / "global", tag_filter=project_id)
    elif scope == "function":
        if not project_id or not function_id:
            return []
        _scan_dir(KB_DATA_DIR / "functions" / project_id / function_id / (kb_type or "general"))
    return out


import pathlib  # 上面 _scan_dir 用到


def _get_index(
    scope: str,
    project_id: Optional[str],
    function_id: Optional[str] = None,
    kb_type: Optional[str] = None,
) -> _Index:
    """读缓存，没有就建。"""
    key = _cache_key(scope, project_id, function_id, kb_type)
    with _lock:
        idx = _cache.get(key)
        if idx is None:
            idx = _Index()
            idx.build(_gather_chunks(scope, project_id, function_id, kb_type))
            _cache[key] = idx
        return idx


def invalidate(
    scope: str,
    project_id: Optional[str] = None,
    function_id: Optional[str] = None,
    kb_type: Optional[str] = None,
) -> None:
    """文档增删时调用。"""
    key = _cache_key(scope, project_id, function_id, kb_type)
    with _lock:
        _cache.pop(key, None)


def invalidate_all() -> None:
    with _lock:
        _cache.clear()


# ============================================================
# 公共接口
# ============================================================
def search(
    query: str,
    scope: str = "global",
    project_id: Optional[str] = None,
    function_id: Optional[str] = None,
    kb_type: Optional[str] = None,
    top_k: int = 5,
    include_global_when_project: bool = True,
) -> List[Dict]:
    """检索。
    
    - scope=global：仅全局
    - scope=project：项目级；若 include_global_when_project=True，也合并全局结果
    - scope=function：仅指定功能知识库；不会混入项目或全局
    """
    if scope == "global":
        idx = _get_index("global", None)
        return idx.search(query, top_k=top_k)
    if scope == "function":
        idx = _get_index("function", project_id, function_id=function_id, kb_type=kb_type or "general")
        return idx.search(query, top_k=top_k)

    # project：项目优先 + 全局兜底
    proj_idx = _get_index("project", project_id)
    proj_results = proj_idx.search(query, top_k=top_k)
    if not include_global_when_project:
        return proj_results

    glob_idx = _get_index("global", None)
    glob_results = glob_idx.search(query, top_k=top_k)
    # 合并 + 去重 + 重排
    merged = proj_results + glob_results
    merged.sort(key=lambda x: x["score"], reverse=True)
    # 简单去重（按 chunk_id）
    seen = set()
    out = []
    for c in merged:
        cid = c.get("chunk_id")
        if cid in seen:
            continue
        seen.add(cid)
        out.append(c)
        if len(out) >= top_k:
            break
    return out
