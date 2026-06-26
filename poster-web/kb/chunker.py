"""文本切片：把长文档切成 LLM/检索可用的小块。

策略：
1. 先按"段落空行"硬切（保留语义边界）
2. 段落过长则按"句号/问号/感叹号/换行"软切
3. 累积到 ~CHUNK_SIZE 字（中文按字符数，英文按词数粗估）就成一块
4. 块之间留 OVERLAP 字重叠（防止关键句被切断）

接口：chunk(text: str) -> list[str]
"""
import re
from typing import List


CHUNK_SIZE = 600  # 每块目标长度（字符）
OVERLAP = 80       # 块间重叠字符数
MAX_CHUNKS = 200   # 单文档最多切片数（防爆）


_SENT_RE = re.compile(r"(?<=[。！？!?\n])")


def chunk(text: str) -> List[str]:
    """把 text 切成不超过 CHUNK_SIZE 字符的块，块之间有 OVERLAP 重叠。"""
    if not text or not text.strip():
        return []

    # 先按段落（连续空行）切
    paras = re.split(r"\n\s*\n", text)
    paras = [p.strip() for p in paras if p.strip()]

    chunks: List[str] = []
    buf = ""

    def _flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
        buf = ""

    for para in paras:
        if len(para) > CHUNK_SIZE:
            # 长段落进一步按句子切
            sents = [s for s in _SENT_RE.split(para) if s.strip()]
            for s in sents:
                if len(buf) + len(s) > CHUNK_SIZE and buf:
                    _flush()
                    # overlap：保留上一块的尾巴
                    if chunks and OVERLAP > 0:
                        buf = chunks[-1][-OVERLAP:]
                buf += s
                if len(buf) >= CHUNK_SIZE:
                    _flush()
        else:
            if len(buf) + len(para) > CHUNK_SIZE and buf:
                _flush()
                if chunks and OVERLAP > 0:
                    buf = chunks[-1][-OVERLAP:]
            buf += ("\n\n" if buf else "") + para

    _flush()

    # 保护：截断到 MAX_CHUNKS
    if len(chunks) > MAX_CHUNKS:
        chunks = chunks[:MAX_CHUNKS]

    return chunks
