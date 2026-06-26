"""中文友好的换行器（v0.6 新增）

旧版 _wrap_text 的问题：
- 严格按字符宽度切，标点会甩到行首（"，" "。" 起头）
- 中英文混排时英文单词会被劈开（"Tencent" → "Tenc / ent"）
- 末尾单字孤行（最后一行只有 1-2 字）
- 不识别"无法折在一起"的双字搭配

v0.6 重写要点：
1. **行首禁排**：右括号/句末标点不能起头 → 上一行多吃一字
2. **行尾禁排**：左括号/起始标点不能结尾 → 下放到下一行
3. **不破词**：连续 ASCII 字母/数字视为一个原子单位，不允许拆分
4. **孤行回吞**：最后一行只有 1 个 CJK 字符时，从上一行末尾让 1 字下来
5. **保留显式换行符 \n**

依赖纯标准库，不引 jieba（避免 skill 安装时多一层依赖）。
中文词级断词不依赖语料，只做"标点正确 + 不破英文词 + 防孤行"。
经验上对训练海报的标题/段落已经够用。
"""
from __future__ import annotations
from typing import List


# 行首禁排集（这些字符不能出现在新行的开头，要把它们留在上一行末尾）
LEAD_FORBIDDEN = set("、。，．,.!?！？；：;:）)】〕」』》〉〗"
                     "％%‰℃℉")
# 行尾禁排集（这些字符不能出现在行尾，应把它们推到下一行开头）
TAIL_FORBIDDEN = set("（(【〔「『《〈〖")
# ASCII 字母/数字 + 连字符（视为不可拆分的原子）
def _is_word_char(ch: str) -> bool:
    return ch.isascii() and (ch.isalnum() or ch in "-'_/.")


def _measure(font, text: str) -> int:
    if not text:
        return 0
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def _tokenize(text: str) -> List[str]:
    """把字符串切成「token 列表」：
       - 单个 CJK 字符 = 1 token
       - 连续 ASCII 词 = 1 token
       - 单个标点 = 1 token
       - 空格 = 1 token（保留给行内排版用）
    """
    tokens: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\n":
            tokens.append("\n")
            i += 1
        elif _is_word_char(ch):
            j = i + 1
            while j < n and _is_word_char(text[j]):
                j += 1
            tokens.append(text[i:j])
            i = j
        else:
            tokens.append(ch)
            i += 1
    return tokens


def wrap_cjk(text: str, font, max_width: int) -> List[str]:
    """中文友好换行。返回每行字符串（不含 \n）。"""
    if not text:
        return [""]
    tokens = _tokenize(text)
    lines: List[str] = []
    cur = ""
    i = 0
    while i < len(tokens):
        tk = tokens[i]
        if tk == "\n":
            lines.append(cur); cur = ""; i += 1; continue

        # 行尾禁排：上一字符是 TAIL_FORBIDDEN，要拖到下一行
        # 实际策略：先 trial，trial 通过再确认；trial 不过先尝试 break。

        trial = cur + tk
        if _measure(font, trial) <= max_width:
            cur = trial
            i += 1
            continue

        # 装不下：要换行
        if cur == "":
            # tk 自己就超宽（极长英文词或大字号单字），强制单字断
            # 把 tk 按字符切，逐字加，至少塞 1 个字符
            chunk = ""
            for ch in tk:
                if _measure(font, chunk + ch) <= max_width:
                    chunk += ch
                else:
                    if chunk:
                        lines.append(chunk)
                        chunk = ch
                    else:
                        # 单字符就超宽，硬塞一个
                        lines.append(ch)
                        chunk = ""
            cur = chunk
            i += 1
            continue

        # 行首禁排：tk 是 LEAD_FORBIDDEN，必须留在当前行
        # 即使超宽也强行塞下（仅 1-2 个标点宽度，影响有限）
        if tk in LEAD_FORBIDDEN:
            cur += tk
            i += 1
            continue

        # 行尾禁排：当前 cur 末尾是 TAIL_FORBIDDEN，要把这个尾字符甩到下一行
        if cur and cur[-1] in TAIL_FORBIDDEN:
            tail = cur[-1]
            before = cur[:-1]
            # 防止无限循环：如果去掉 tail 后 before 为空，说明 tail 本身就是新行的开头
            # 此时强制把 tail 留在当前行（即正常换行不做行尾禁排处理）
            if not before:
                lines.append(cur)
                cur = tk
                i += 1
                continue
            lines.append(before)
            cur = tail
            # 当前 tk 还没消费，下一轮再来
            continue

        # 普通换行
        lines.append(cur)
        cur = tk
        i += 1

    if cur:
        lines.append(cur)

    # 孤行回吞：最后一行只剩 1 个 CJK 字符（且不是标点），从上一行借 1 字
    if len(lines) >= 2 and len(lines[-1]) == 1:
        ch = lines[-1]
        if not ch.isascii() and ch not in LEAD_FORBIDDEN and ch not in TAIL_FORBIDDEN:
            prev = lines[-2]
            if len(prev) >= 2:
                lines[-2] = prev[:-1]
                lines[-1] = prev[-1] + ch
    # 行首孤标点纠正：再扫一遍把 LEAD_FORBIDDEN 起头的塞回上一行末尾（避免极端情况）
    fixed: List[str] = []
    for ln in lines:
        if fixed and ln and ln[0] in LEAD_FORBIDDEN:
            # 把首字符附到上一行末尾（如果上一行加上去仍能渲染）
            fixed[-1] = fixed[-1] + ln[0]
            ln = ln[1:]
        fixed.append(ln)
    return fixed if fixed else [""]


def draw_multiline_cjk(draw, xy, text, font, fill, line_h, max_width,
                       stroke_width=0, stroke_fill=None) -> int:
    """带中文换行的多行文字。返回结束 y。"""
    x, y = xy
    for line in wrap_cjk(text, font, max_width):
        if stroke_width and stroke_fill:
            draw.text((x, y), line, font=font, fill=fill,
                      stroke_width=stroke_width, stroke_fill=stroke_fill)
        else:
            draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y
