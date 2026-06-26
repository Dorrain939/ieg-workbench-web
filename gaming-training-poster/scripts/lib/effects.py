"""
视觉效果工具集 —— 阴影、光影、渐变、磨砂、噪点。

这一层是 v0.4 的新增。所有组件 / 背景都经过这里包装，
统一获得"有质感、有空间感"的视觉语言，避免纯色平面感。

核心原则：
- 所有效果都返回 RGBA Image 或在 canvas 上 alpha_composite，不破坏底图。
- 阴影统一用 GaussianBlur + 偏移；高光统一用 alpha 渐变带。
- 字体描边/外发光通过多次偏移绘制 + GaussianBlur 实现。
"""
from __future__ import annotations
import math
import random
from typing import Tuple, Optional, List

from PIL import Image, ImageDraw, ImageFilter, ImageChops

from .palette import hex_to_rgb
from .text_layout import wrap_cjk


# ============================================================
# 1. drop_shadow —— 给任意 RGBA 图层打阴影
# ============================================================
def drop_shadow(
    layer: Image.Image,
    offset: Tuple[int, int] = (0, 12),
    blur: int = 24,
    color: Tuple[int, int, int] = (0, 0, 0),
    alpha: int = 140,
) -> Image.Image:
    """生成一张比原 layer 大一圈的阴影图（含原图）。

    返回的图尺寸 = (w + 2*pad, h + 2*pad)，pad = blur + max(|dx|,|dy|)。
    粘贴时左上角对齐到原 layer 的 (x0 - pad, y0 - pad) 即可。
    """
    dx, dy = offset
    pad = blur + max(abs(dx), abs(dy)) + 4
    w, h = layer.size
    out = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

    # 用 layer 的 alpha 通道生成阴影遮罩
    alpha_ch = layer.split()[-1] if layer.mode == "RGBA" else layer.convert("L")
    shadow_mask = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    shadow_mask.paste(alpha_ch, (pad + dx, pad + dy))
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(blur))

    # 阴影色块
    shadow = Image.new("RGBA", out.size, color + (alpha,))
    out.paste(shadow, (0, 0), shadow_mask)

    # 原层粘在最上面
    out.alpha_composite(layer, (pad, pad))
    return out, pad


def paste_with_shadow(
    canvas: Image.Image,
    layer: Image.Image,
    xy: Tuple[int, int],
    offset: Tuple[int, int] = (0, 12),
    blur: int = 24,
    color: Tuple[int, int, int] = (0, 0, 0),
    alpha: int = 140,
):
    """便捷函数：直接把带阴影的 layer 贴到 canvas 上的 (x, y)。"""
    out, pad = drop_shadow(layer, offset, blur, color, alpha)
    x, y = xy
    canvas.alpha_composite(out, (x - pad, y - pad))


# ============================================================
# 2. inner_highlight —— 给面板顶部加一道半透明白色高光
# ============================================================
def inner_highlight(
    layer: Image.Image,
    radius: int = 18,
    height_ratio: float = 0.5,
    alpha_top: int = 90,
    alpha_bottom: int = 0,
) -> Image.Image:
    """在 RGBA 面板上叠加一层从顶到中间的白色渐变高光。

    用于按钮、徽章、卡片头部，制造"光从上方打下来"的体积感。
    """
    w, h = layer.size
    hl_h = int(h * height_ratio)
    hl = Image.new("RGBA", (w, hl_h), (0, 0, 0, 0))
    pixels = hl.load()
    for y in range(hl_h):
        t = y / max(hl_h - 1, 1)
        a = int(alpha_top + (alpha_bottom - alpha_top) * t)
        for x in range(w):
            pixels[x, y] = (255, 255, 255, a)

    # 圆角裁剪
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    out = layer.copy()
    hl_full = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hl_full.paste(hl, (0, 0))
    hl_masked = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hl_masked.paste(hl_full, (0, 0), mask)
    out.alpha_composite(hl_masked)
    return out


# ============================================================
# 3. gradient_fill —— 生成线性 / 径向渐变填充图
# ============================================================
def linear_gradient(
    size: Tuple[int, int],
    color_a: str,
    color_b: str,
    direction: str = "vertical",
) -> Image.Image:
    """direction: vertical | horizontal | diagonal-tl-br | diagonal-tr-bl"""
    w, h = size
    img = Image.new("RGB", size, color_a)
    pixels = img.load()
    ra, ga, ba = hex_to_rgb(color_a)
    rb, gb, bb = hex_to_rgb(color_b)

    if direction == "vertical":
        for y in range(h):
            t = y / max(h - 1, 1)
            r = int(ra + (rb - ra) * t)
            g = int(ga + (gb - ga) * t)
            b = int(ba + (bb - ba) * t)
            for x in range(w):
                pixels[x, y] = (r, g, b)
    elif direction == "horizontal":
        for x in range(w):
            t = x / max(w - 1, 1)
            r = int(ra + (rb - ra) * t)
            g = int(ga + (gb - ga) * t)
            b = int(ba + (bb - ba) * t)
            for y in range(h):
                pixels[x, y] = (r, g, b)
    else:  # 对角
        for y in range(h):
            for x in range(w):
                t = (x + y) / max(w + h - 2, 1)
                r = int(ra + (rb - ra) * t)
                g = int(ga + (gb - ga) * t)
                b = int(ba + (bb - ba) * t)
                pixels[x, y] = (r, g, b)
    return img.convert("RGBA")


def radial_glow(
    size: Tuple[int, int],
    center: Tuple[int, int],
    radius: int,
    color: str = "#FFFFFF",
    alpha_center: int = 180,
) -> Image.Image:
    """以 center 为圆心，从 alpha_center 衰减到 0 的径向光晕。返回 RGBA Image。"""
    w, h = size
    cx, cy = center
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = img.load()
    cr, cg, cb = hex_to_rgb(color)
    r2 = radius * radius
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            d2 = dx * dx + dy * dy
            if d2 > r2:
                continue
            t = math.sqrt(d2) / radius
            a = int(alpha_center * (1 - t) ** 2)
            pixels[x, y] = (cr, cg, cb, a)
    return img


# ============================================================
# 4. noise_grain —— 生成可叠加的噪点层
# ============================================================
def noise_grain(size: Tuple[int, int], strength: int = 12, seed: int = 42) -> Image.Image:
    """alpha 介于 0~strength 的随机噪点。叠加在背景上能消除"塑料感"。"""
    w, h = size
    rng = random.Random(seed)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            v = rng.randint(0, strength)
            # 黑白 mix（随机选）
            if rng.random() < 0.5:
                pixels[x, y] = (255, 255, 255, v)
            else:
                pixels[x, y] = (0, 0, 0, v)
    return img


def fast_noise_grain(
    size: Tuple[int, int],
    strength: int = 12,
    seed: int = 42,
    scale: int = 2,
) -> Image.Image:
    """快速噪点：先生成 1/scale 尺寸再放大。

    v0.9.4 修复：scale 默认从 4 降到 2，并改用 BILINEAR 而非 NEAREST。
    NEAREST + scale=4 等于把每个噪点像素硬放大成 4×4 块，
    叠到大块浅色（米色/白色）上时眼睛能直接看到 4 像素马赛克。
    BILINEAR 会做插值，且 scale=2 时颗粒已足够小，肉眼基本看不到块。
    速度损失约 4 倍但仍远快于像素级噪点。
    """
    w, h = size
    s = max(1, int(scale))
    sw, sh = max(w // s, 1), max(h // s, 1)
    small = noise_grain((sw, sh), strength, seed)
    return small.resize((w, h), Image.BILINEAR)


# ============================================================
# 4.5 chroma_key_to_alpha —— 把 RGB 图按"亮度+饱和度"抠成 RGBA
# ============================================================
def chroma_key_to_alpha(
    img: Image.Image,
    bg_lightness_min: int = 140,
    bg_saturation_max: int = 50,
    softness: int = 30,
    invert: bool = False,
    bg_kind: str = "auto",
    bg_darkness_max: int = 35,
    edge_clean: bool = True,
) -> Image.Image:
    """把 AI 出图的纯色背景"抠"成透明，保留主体。

    很多 AI 图像 API（包括 nano banana / 通义万相默认导出）即便要求
    "transparent background"，也会给一张 **RGB** 图，背景是浅灰、纯白或纯黑。
    直接 .convert("RGBA") 拿到的 alpha 还是 255，贴到画布上就是色块。

    现在支持两类背景：
        bg_kind="light"：浅灰/白底 + 深色或彩色主体（旧逻辑）
        bg_kind="dark" ：深黑/深灰底 + 高饱和或浅色主体（艺术字常见）
        bg_kind="auto" ：自动判断——取四角 24px 区域的平均亮度，
                        ≥ 140 视作 light，≤ 60 视作 dark，否则按 light 兜底。

    判定背景的双门槛（同时满足才算背景）：
        light: 亮度 ≥ bg_lightness_min  且  饱和度 ≤ bg_saturation_max
        dark : 亮度 ≤ bg_darkness_max   且  饱和度 ≤ bg_saturation_max

    softness 区间内做线性过渡，避免硬边。

    edge_clean=True 时再做一遍 alpha 形态学：用 alpha 自身做 GaussianBlur 后
    乘回去，去掉残留的"灰色光晕"硬边。

    Args:
        bg_lightness_min: light 模式下，亮度 ≥ 该值才判为背景，默认 140
        bg_darkness_max:  dark 模式下，亮度 ≤ 该值才判为背景，默认 35
        bg_saturation_max: 饱和度 (max-min) ≤ 该值才判为背景，默认 50
        softness: 边缘软过渡区间，默认 30
        invert: 兼容旧 API，置 True 等价于切换到反向（light↔dark）
        bg_kind: "auto" | "light" | "dark"
        edge_clean: 是否做边缘清理
    """
    import numpy as np
    arr = np.array(img.convert("RGB")).astype(np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    lightness = (r.astype(np.float32) + g + b) / 3.0
    saturation = (arr.max(axis=-1) - arr.min(axis=-1)).astype(np.float32)

    H, W = lightness.shape
    # ---- auto 检测：取四角 + 中心顶 / 底 1 像素带的均值 ----
    if bg_kind == "auto":
        sample = max(8, min(W, H) // 24)
        corners = np.concatenate([
            lightness[:sample, :sample].ravel(),
            lightness[:sample, -sample:].ravel(),
            lightness[-sample:, :sample].ravel(),
            lightness[-sample:, -sample:].ravel(),
        ])
        edge_mean = float(corners.mean())
        if edge_mean <= 70:
            bg_kind = "dark"
        elif edge_mean >= 140:
            bg_kind = "light"
        else:
            # 中间灰也按 light 处理，但门槛下调
            bg_kind = "light"
            bg_lightness_min = max(100, int(edge_mean) - 10)

    if invert:
        bg_kind = "dark" if bg_kind == "light" else "light"

    # ---- 计算 bg_score（0=非背景, 1=纯背景） ----
    soft = max(softness, 1)
    if bg_kind == "dark":
        # 暗：亮度越低越背景
        light_t = bg_darkness_max + softness  # 高于该值一定是前景
        bg_light_score = np.clip((light_t - lightness) / soft, 0, 1)
    else:
        # 亮：亮度越高越背景
        light_t = bg_lightness_min - softness  # 低于该值一定是前景
        bg_light_score = np.clip((lightness - light_t) / soft, 0, 1)
    sat_t = bg_saturation_max + softness
    bg_sat_score = np.clip((sat_t - saturation) / soft, 0, 1)
    bg_score = bg_light_score * bg_sat_score
    alpha = ((1.0 - bg_score) * 255).clip(0, 255).astype(np.uint8)

    # ---- 边缘清理：alpha 自卷积，把"半透明灰晕"压平 ----
    if edge_clean:
        alpha_img = Image.fromarray(alpha, mode="L")
        # 一次轻模糊 + 反向 Gamma：把 0~120 推 0、180~255 推 255、中间保留软过渡
        alpha_blur = alpha_img.filter(ImageFilter.GaussianBlur(1.2))
        ab = np.array(alpha_blur).astype(np.float32) / 255.0
        # gamma 1.4 让中间偏低
        ab = np.clip((ab - 0.15) / 0.7, 0, 1) ** 0.85
        alpha = (ab * 255).clip(0, 255).astype(np.uint8)

    rgba = np.dstack([arr.astype(np.uint8), alpha])
    return Image.fromarray(rgba, mode="RGBA")


def recolor_with_mask(img_rgba: Image.Image, fill_color: str,
                      gradient_color: Optional[str] = None) -> Image.Image:
    """把已经抠出 alpha 的图，用单色或渐变重染前景。

    使用场景：AI 出的艺术字往往是黑色或灰色字，抠出后贴到深色背景上看不清。
    这时候用品牌 accent 色重新染色一遍，再贴入。

    渐变方向固定为竖向 top→bottom（艺术字常见）。
    """
    import numpy as np
    arr = np.array(img_rgba.convert("RGBA"))
    h, w = arr.shape[:2]
    alpha = arr[..., 3]

    fr, fg, fb = hex_to_rgb(fill_color)
    if gradient_color:
        gr, gg, gb = hex_to_rgb(gradient_color)
        # 竖向渐变
        ramp = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        rch = (fr * (1 - ramp) + gr * ramp).astype(np.uint8)
        gch = (fg * (1 - ramp) + gg * ramp).astype(np.uint8)
        bch = (fb * (1 - ramp) + gb * ramp).astype(np.uint8)
        rch = np.broadcast_to(rch, (h, w))
        gch = np.broadcast_to(gch, (h, w))
        bch = np.broadcast_to(bch, (h, w))
        out = np.dstack([rch, gch, bch, alpha]).astype(np.uint8)
    else:
        out = np.zeros_like(arr)
        out[..., 0] = fr
        out[..., 1] = fg
        out[..., 2] = fb
        out[..., 3] = alpha
    return Image.fromarray(out, mode="RGBA")


# ============================================================
# 5. text_with_glow —— 带外发光的文字
# ============================================================
def text_with_glow(
    canvas: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font,
    fill: str = "#FFFFFF",
    glow_color: str = "#FBBF24",
    glow_blur: int = 12,
    glow_alpha: int = 200,
    stroke_width: int = 0,
    stroke_fill: Optional[str] = None,
):
    """先在临时层画发光底，再画主体字。"""
    x, y = xy
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0] + glow_blur * 4
    th = bbox[3] - bbox[1] + glow_blur * 4
    pad = glow_blur * 2

    glow_layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gr, gg, gb = hex_to_rgb(glow_color)
    gd.text((pad - bbox[0], pad - bbox[1]), text, font=font, fill=(gr, gg, gb, glow_alpha))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow_blur))
    canvas.alpha_composite(glow_layer, (x - pad + bbox[0], y - pad + bbox[1]))

    d = ImageDraw.Draw(canvas)
    if stroke_width > 0 and stroke_fill:
        d.text((x, y), text, font=font, fill=fill,
               stroke_width=stroke_width, stroke_fill=stroke_fill)
    else:
        d.text((x, y), text, font=font, fill=fill)


def text_with_gradient(
    canvas: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font,
    color_a: str = "#FFD66B",
    color_b: str = "#FF6B6B",
    direction: str = "vertical",
    stroke_width: int = 0,
    stroke_fill: Optional[str] = None,
):
    """渐变填充的文字（先画到 mask，用渐变图按 mask 贴到 canvas）。"""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 12
    if tw <= 0 or th <= 0:
        return
    # mask
    mask = Image.new("L", (tw, th), 0)
    md = ImageDraw.Draw(mask)
    if stroke_width > 0 and stroke_fill:
        # 在 mask 上画文字（白色），描边另外画
        md.text((-bbox[0], -bbox[1]), text, font=font, fill=255,
                stroke_width=stroke_width, stroke_fill=255)
    else:
        md.text((-bbox[0], -bbox[1]), text, font=font, fill=255)
    # 渐变层
    grad = linear_gradient((tw, th), color_a, color_b, direction)
    # 合成
    text_layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    text_layer.paste(grad, (0, 0), mask)
    x, y = xy
    canvas.alpha_composite(text_layer, (x, y))
    # 再画一遍描边以保持锐利
    if stroke_width > 0 and stroke_fill:
        d = ImageDraw.Draw(canvas)
        # 只画描边不画填充：trick 是用 fill 同色但 stroke 在外
        # PIL 不支持单独画 stroke，这里近似：透明 fill 不行，所以用先描边再渐变填充覆盖的策略已被上面 mask 覆盖。
        pass


# ============================================================
# 6. rounded_panel —— 一站式生成"高级感"面板
# ============================================================
def rounded_panel(
    size: Tuple[int, int],
    fill: str = "#FFFFFF",
    fill_b: Optional[str] = None,
    radius: int = 18,
    alpha: int = 255,
    border_color: Optional[str] = None,
    border_width: int = 0,
    add_highlight: bool = True,
    direction: str = "vertical",
) -> Image.Image:
    """生成一块圆角面板（可选渐变填充 + 内高光 + 描边）。"""
    w, h = size
    if fill_b:
        bg = linear_gradient((w, h), fill, fill_b, direction)
    else:
        r, g, b = hex_to_rgb(fill)
        bg = Image.new("RGBA", (w, h), (r, g, b, 255))

    # 圆角裁剪
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=alpha)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)

    if add_highlight:
        out = inner_highlight(out, radius=radius, height_ratio=0.5,
                              alpha_top=70, alpha_bottom=0)

    if border_color and border_width > 0:
        bd_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(bd_layer).rounded_rectangle(
            [border_width // 2, border_width // 2,
             w - border_width // 2, h - border_width // 2],
            radius=radius, outline=border_color, width=border_width)
        out.alpha_composite(bd_layer)

    return out


# ============================================================
# 7. text_chip —— 文字 + 圆角底框（v0.6 新增，替代描边方案）
# ============================================================
def text_chip(
    canvas: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font,
    fg: str = "#FFFFFF",
    bg: str = "#0E0F1A",
    bg_alpha: int = 200,
    radius: int = 10,
    padding: Tuple[int, int] = (14, 6),
    border_color: Optional[str] = None,
    border_width: int = 0,
) -> Tuple[int, int]:
    """画一个"文字+底框"的 chip（atomic 操作）。
    返回 chip 的 (width, height)，方便外部计算下一行 / 下一列起点。

    用法场景：
    - meta_row 的 label/value：每个一个 chip，区别于背景
    - lead_paragraph / qa_block 的小字单行：套个浅底 chip 提对比度
    - schedule_table 的列头单元格

    设计选择：单行优先。多行文字请用 draw_text_block + panel。
    """
    px, py = padding
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    chip_w = tw + px * 2
    chip_h = th + py * 2 + 4
    x, y = xy

    chip = Image.new("RGBA", (chip_w, chip_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(chip)
    r, g, b = hex_to_rgb(bg)
    cd.rounded_rectangle([0, 0, chip_w, chip_h], radius=radius,
                          fill=(r, g, b, bg_alpha))
    if border_color and border_width > 0:
        bdr, bdg, bdb = hex_to_rgb(border_color)
        cd.rounded_rectangle([border_width // 2, border_width // 2,
                              chip_w - border_width // 2, chip_h - border_width // 2],
                             radius=radius, outline=(bdr, bdg, bdb, 255),
                             width=border_width)
    canvas.alpha_composite(chip, (x, y))

    d = ImageDraw.Draw(canvas)
    # text 的基线偏移由 bbox 决定（不同字体 bbox top 不为 0）
    d.text((x + px - bbox[0], y + py - bbox[1] + 2), text, font=font, fill=fg)
    return chip_w, chip_h


def measure_chip(text: str, font, padding: Tuple[int, int] = (14, 6)) -> Tuple[int, int]:
    """返回 chip 占的 (w, h)，外部布局可以预先排版。"""
    px, py = padding
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    return tw + px * 2, th + py * 2 + 4


# ============================================================
# 8. draw_text_block —— 在已有面板内画多行中文（无描边）
# ============================================================
def draw_text_block(
    canvas: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font,
    fill: str,
    line_h: int,
    max_width: int,
) -> int:
    """中文友好换行 + 无描边纯字。返回结束 y。
    专给已套了 panel 的正文用——靠面板的对比度，不靠描边。
    """
    d = ImageDraw.Draw(canvas)
    x, y = xy
    for line in wrap_cjk(text, font, max_width):
        d.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


def draw_text_block_with_shadow(
    canvas: Image.Image,
    xy: Tuple[int, int],
    text: str,
    font,
    fill: str,
    line_h: int,
    max_width: int,
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    shadow_alpha: int = 100,
    shadow_offset: Tuple[int, int] = (0, 2),
) -> int:
    """无描边但加柔和投影 —— 适合放在底图（AI图）上的小标签。
    比 stroke 更柔，不会让字形糊。"""
    x, y = xy
    dx, dy = shadow_offset
    for line in wrap_cjk(text, font, max_width):
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0] + 16
        th = bbox[3] - bbox[1] + 16
        sh_layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        ImageDraw.Draw(sh_layer).text(
            (8 - bbox[0], 8 - bbox[1]), line, font=font,
            fill=(*shadow_color, shadow_alpha))
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(2))
        canvas.alpha_composite(sh_layer, (x - 8 + dx, y - 8 + dy))
        ImageDraw.Draw(canvas).text((x, y), line, font=font, fill=fill)
        y += line_h
    return y
