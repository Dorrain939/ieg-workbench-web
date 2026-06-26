"""
散点装饰引擎 v0.5 —— 按禁飞区反推安全区，支持真实装饰 PNG。

变化点（v0.5）
==============
1. **PlacementMap 禁飞区**：scatter 时读 ctx.occupied，候选位置必须不与任何
   组件 bbox 相交，否则丢弃重抽；最多尝试 N 次仍找不到位置就放弃这一颗，
   保证文字一定不会被遮。
2. **真实装饰 PNG 兼容**：deco_cfg.types 元素可以是字符串（内置形状），
   也可以是字典 `{ "name": str, "path": str, "size": [min, max] }`。
   path 存在则从磁盘加载并按尺寸缩放贴上；否则退化到自绘。
3. **尺寸自适应**：每张装饰按 deco_cfg.density 决定基础尺寸，并按其在画布
   纵向位置（top/middle/bottom）轻微缩放，避免远近一致的"贴纸感"。
4. **避免互相重叠**：保留 v0.4 的 placed 列表去重，门槛缩小到 size。

约定
====
- 装饰只允许出现在「未被组件 reserve」的区域；
- 装饰永远比组件**层级更低**——本函数会在 compose 流末尾调用，但内部使用
  `composite_below_text` 实现：先把已有 canvas 拍平为 base，再把装饰画到 base
  上，最后把组件文字层覆盖回来。如果你不需要这种层级控制，直接 alpha_composite
  到 canvas 也可以接受（默认行为）。
"""
from __future__ import annotations
import random
from pathlib import Path
from typing import List, Tuple, Union, Dict

from PIL import Image, ImageDraw

from .context import RenderContext
from .palette import hex_to_rgb


DENSITY_COUNT = {"low": 4, "medium": 8, "high": 14}
DENSITY_SIZE = {"low": (28, 56), "medium": (32, 72), "high": (36, 96)}


def scatter(canvas: Image.Image, ctx: RenderContext, deco_cfg: dict):
    """按 deco_cfg 在 canvas 上撒装饰，自动避开 ctx.occupied 禁飞区。

    deco_cfg 字段：
      - density: low | medium | high
      - types: List[str | dict]
                str  → 内置形状（floating_chars/paper_planes/crystals/pixel_burst/code_glyphs）
                dict → 真实素材：{ "name": "snowflake", "path": "/abs/path.png",
                                  "size": [40, 96] }
      - seed: int
      - exclude_top, exclude_bottom: 顶/底裁切像素（默认按 hero/footer 留边）
    """
    types = deco_cfg.get("types", ["floating_chars", "paper_planes", "crystals"])
    density = deco_cfg.get("density", "medium")
    count = int(deco_cfg.get("count", DENSITY_COUNT.get(density, 8)))
    size_min, size_max = DENSITY_SIZE.get(density, (32, 72))
    rng = random.Random(deco_cfg.get("seed", 42))

    w, h = canvas.size
    top_pad = deco_cfg.get("exclude_top", 40)
    bot_pad = deco_cfg.get("exclude_bottom", 220)

    placed: List[Tuple[int, int, int]] = []   # (x, y, size)
    attempts = 0
    max_attempts = count * 30   # 避免死循环
    while len(placed) < count and attempts < max_attempts:
        attempts += 1
        kind = rng.choice(types)
        # type 自带 size 范围则覆盖全局
        if isinstance(kind, dict) and kind.get("size"):
            ksize = kind["size"]
            size = rng.randint(int(ksize[0]), int(ksize[1]))
        else:
            size = rng.randint(size_min, size_max)
        x = rng.randint(20, w - size - 20)
        y = rng.randint(top_pad, h - bot_pad - size)

        # 1) 与已放置的装饰互相避让
        if any(abs(x - px) < max(140, size) and abs(y - py) < max(140, size)
               for px, py, _ in placed):
            continue

        # 2) 不能落到 reserve 出来的禁飞区（文字/卡片）
        if not ctx.is_safe((x, y, x + size, y + size)):
            continue

        placed.append((x, y, size))
        _draw_one(canvas, ctx, x, y, size, kind, rng)

    if attempts >= max_attempts:
        print(f"[decorations] 仅放置 {len(placed)}/{count} 个装饰，"
              f"原因：禁飞区过密（已尝试 {attempts} 次）")


# ============================================================
# 单元渲染：内置形状 + 真实 PNG 双路径
# ============================================================
def _draw_one(canvas: Image.Image, ctx: RenderContext, x: int, y: int,
              size: int, kind: Union[str, Dict], rng: random.Random):
    # 真实装饰 PNG 路径
    if isinstance(kind, dict):
        path = kind.get("path")
        if path and Path(path).exists():
            try:
                deco = Image.open(path).convert("RGBA")
                # 等比缩放：以 size 作为长边
                ratio = size / max(deco.size)
                new_size = (int(deco.width * ratio), int(deco.height * ratio))
                deco = deco.resize(new_size, Image.LANCZOS)
                # 轻微旋转，破"贴纸感"
                if kind.get("rotate", True):
                    deco = deco.rotate(rng.randint(-15, 15), resample=Image.BICUBIC,
                                       expand=True)
                canvas.alpha_composite(deco, (x, y))
                return
            except Exception as e:
                print(f"[decorations] 加载装饰 {path} 失败: {e}")
        # v0.9.10：零占位铁律 —— 没 path 或加载失败时直接 return，
        # 不再退化到内置 PIL 形状（小方块/小圆点/占位企鹅，丑且无意义）。
        return

    # v0.9.10：仅字符串 kind（无 path）也直接 return，不再画内置形状。
    return


def _draw_paper_plane(d, x, y, s, color):
    d.polygon([(x, y), (x + s, y + s // 2), (x, y + s),
               (x + s // 3, y + s // 2)], fill=color)


def _draw_crystal(d, x, y, s, color):
    d.polygon([(x + s // 2, y), (x + s, y + s // 2),
               (x + s // 2, y + s), (x, y + s // 2)],
              fill=color, outline="#FFFFFF")


def _draw_pixel_burst(d, x, y, s, color):
    cell = max(s // 4, 6)
    pattern = [(0, 0), (1, 0), (0, 1), (2, 1), (1, 2), (3, 2), (2, 3)]
    for dx, dy in pattern:
        d.rectangle([x + dx * cell, y + dy * cell,
                     x + (dx + 1) * cell, y + (dy + 1) * cell], fill=color)


def _draw_floating_char(d, x, y, s, c1, c2, rng):
    """企鹅/像素小人剪影占位：椭圆 + 圆 + 两脚。"""
    # 身体
    d.ellipse([x, y + s // 3, x + s, y + s], fill="#0E0F1A")
    # 肚子
    d.ellipse([x + s // 5, y + s // 2, x + s - s // 5, y + s - s // 8],
              fill="#FFFFFF")
    # 头
    d.ellipse([x + s // 4, y, x + s - s // 4, y + s // 2], fill="#0E0F1A")
    # 喙
    d.polygon([(x + s // 2 - s // 12, y + s // 4),
               (x + s // 2 + s // 12, y + s // 4),
               (x + s // 2, y + s // 3 + 4)], fill=c1)
    # 眼睛
    er = max(s // 18, 2)
    d.ellipse([x + s // 3 - er, y + s // 6 - er,
               x + s // 3 + er, y + s // 6 + er], fill="#FFFFFF")
    d.ellipse([x + 2 * s // 3 - er, y + s // 6 - er,
               x + 2 * s // 3 + er, y + s // 6 + er], fill="#FFFFFF")


def _draw_code_glyph(d, ctx: RenderContext, x, y, s, color, rng):
    glyph = rng.choice(["</>", "{}", "[ ]", "/*", "01"])
    f = ctx.font(s)
    d.text((x, y), glyph, font=f, fill=color)


def _draw_sparkle(d, x, y, s, color):
    """四角星 sparkle。"""
    cx, cy = x + s // 2, y + s // 2
    arm = s // 2
    d.polygon([(cx, cy - arm), (cx + arm // 4, cy), (cx, cy + arm), (cx - arm // 4, cy)],
              fill=color)
    d.polygon([(cx - arm, cy), (cx, cy + arm // 4), (cx + arm, cy), (cx, cy - arm // 4)],
              fill=color)
