"""
组件渲染库 —— 模块化长图引擎的核心。

每个 render_xxx 遵循契约：
    render(canvas, y_cursor, ctx, data) -> y_next

- canvas: PIL.Image (RGBA)
- y_cursor: 当前 y 写入位置
- ctx: RenderContext（提供 palette / font / margin / content 区宽度 / occupied 禁飞区）
- data: brief 中该 section 的 dict
- 返回值：渲染完成后的下一个 y 位置（不含 SECTION_GAP）

注意：
- 所有视觉常量 (圆角半径 / 标题字号 / 内边距) 都按 1200 宽长图标定。
- 如果未来要支持 1500 / 750 等其它宽度，需要把这些常量按 ctx.width / 1200 缩放。

v0.5 关键变化：
- 字色不再写死 #FFFFFF，统一从 ctx.palette["text_on_dark"] / ["text_on_primary"] / ["text_on_accent_a"]
  取值；如果 palette 没给，再退回 best_text_color(局部底色) 自适应。
- 关键大字加 stroke 描边（halo），落到过渡色带也清晰。
- 每个组件渲染完调用 ctx.reserve(bbox) 注册禁飞区，避免装饰 PNG 遮文字。
"""
from __future__ import annotations
from typing import Optional
import pathlib
import re
import html as html_lib

# ROOT = skill 根目录（scripts/ 的上级），用于解析 brief 里的相对路径
_COMPONENTS_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

def _resolve_path(p: str) -> pathlib.Path:
    """解析路径：绝对路径直接返回，相对路径以 skill 根目录为基准。"""
    pp = pathlib.Path(p)
    if pp.is_absolute():
        return pp
    # 尝试相对于 skill 根目录
    candidate = _COMPONENTS_ROOT / p
    if candidate.exists():
        return candidate
    return pp  # 找不到时返回原始（exists() 会返回 False）

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .context import RenderContext
from .palette import hex_to_rgb, pick_text_color_on
from .palette_lab import best_text_color, halo_color_for
from .text_layout import wrap_cjk
from . import effects as FX
from . import assets as A


# ---------- 工具：字色 ----------
def _text_on(ctx: RenderContext, role: str, fallback_bg: Optional[str] = None) -> str:
    """根据角色取字色：
       role ∈ {dark, primary, accent_a}  → 优先取 palette 中预设的字色
       fallback_bg → 若 palette 没给，则按这个底色用对比度算法挑
    """
    key = f"text_on_{role}"
    val = ctx.palette.get(key)
    if val:
        return val
    if fallback_bg:
        return best_text_color(fallback_bg)
    return "#FFFFFF"


def _brightness(ctx: RenderContext) -> str:
    """读 brief 全局亮度模式：light 时所有信息卡走浅底深字。"""
    bri = None
    if hasattr(ctx, "canvas_cfg") and ctx.canvas_cfg:
        bri = ctx.canvas_cfg.get("_resolved_brightness")
    if not bri:
        bri = getattr(ctx, "brightness", None)
    return bri or "dark"


def _panel_pair(ctx: RenderContext):
    """v0.9.3 铁律：light 模式 → 浅底深字；dark 模式 → 深底白字。
    返回 (panel_fill, text_color)。
    """
    if _brightness(ctx) == "light":
        panel_fill = ctx.palette.get("neutral_panel", "#FFFBF0")
        text_color = ctx.palette.get("text_on_dark", "#1F2937")  # 注意 text_on_dark 在 light 配色里被定义为"用于浅底的深字"
        # 兜底：如果 text_on_dark 仍是浅色，回退黑灰
        if text_color and text_color.upper() in ("#FFFFFF", "#FFF7ED", "#FFF8EE"):
            text_color = "#1F2937"
        return panel_fill, text_color
    else:
        # dark 模式：深底白字
        panel_fill = ctx.palette.get("panel_dark", "#0E0F1A")
        text_color = "#FFFFFF"
        return panel_fill, text_color


def _halo(text_hex: str) -> str:
    return halo_color_for(text_hex)


# ---------- 工具：圆角矩形磨砂面板 ----------

def _frosted_panel(canvas: Image.Image, box, radius=24, alpha=120, fill_hex: Optional[str] = None):
    """画一个圆角磨砂面板。box=(x0,y0,x1,y1)。

    v0.9.10：在 light 模式下，外部很容易传 alpha<=180 让面板半透明，
    导致下方渐变底图（米白→朱红）从 panel 透出，**用户视觉上看到 panel
    背景"由浅变灰变深"**——这是用户反馈"模块底色变成灰色深色"的根因。
    本函数无法直接拿到 ctx，由调用点保证 alpha；这里只补一句注释提醒。
    """
    x0, y0, x1, y1 = box
    panel = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    if fill_hex:
        r, g, b = hex_to_rgb(fill_hex)
        fill = (r, g, b, alpha)
    else:
        fill = (255, 255, 255, alpha)
    pdraw.rounded_rectangle([0, 0, x1 - x0, y1 - y0], radius=radius, fill=fill)
    canvas.alpha_composite(panel, (x0, y0))


def _panel_alpha(ctx: RenderContext, dark_default: int = 215) -> int:
    """v0.9.10：light 模式 panel 一律 255 不透明（米白底纯色，不让渐变透出）。
    dark 模式回退原半透明（保持深底磨砂质感）。"""
    return 255 if _brightness(ctx) == "light" else dark_default


def _wrap_text(text: str, font, max_width: int):
    """v0.6: 走中文友好换行器（避头尾、不破词、防孤行）。"""
    return wrap_cjk(text, font, max_width)


# ---------- 工具：编号/项目符号强制换行 ----------
import re as _re
_BULLET_PATTERN = _re.compile(
    r"(?<!^)(?=(?:"
    r"\s*[·•●◆▪▫■□◇★☆※]\s*"           # 项目符号
    r"|\s*\d{1,2}[\)）.、]\s+"               # 1) 1. 1、 1）
    r"|\s*[（(]\s*\d{1,2}\s*[)）]\s*"       # (1) （1）
    r"|\s*[①-⑳⓪]\s*"                     # 圆圈数字
    r"|\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\s*"            # 罗马数字
    r"|\s*Q\d+\s*[:：]\s*"                   # Q1: Q2:
    r"|\s*A\d+\s*[:：]\s*"                   # A1:
    r"))"
)


def _split_bullet_lines(text: str) -> list:
    """把混在一段里的 1) 2) 3) / · / ① 拆成多段（保留前缀）。
    用户偏好：每个编号/项目符号都另起一行。"""
    if not text:
        return [text]
    # 已含换行的：尊重已有换行
    if "\n" in text:
        return text.split("\n")
    # 1)2)3) 或 ·xxx·yyy 或 ①②③：在符号前插入换行，再拆
    # 启发式：仅当文本里出现 ≥2 处编号/项目符号时才拆
    import re
    matches = _BULLET_PATTERN.findall(text) if False else None
    # 用 finditer 数命中数
    hits = list(_BULLET_PATTERN.finditer(text))
    if len(hits) < 1:
        return [text]
    # split：把每个匹配前插换行
    parts = _BULLET_PATTERN.split(text)
    out = []
    for p in parts:
        p = p.strip()
        if p:
            # 去掉编号/符号后多余空白
            p = re.sub(r"\s+", " ", p).strip()
            out.append(p)
    return out if len(out) >= 2 else [text]


def _wrap_text_block(text: str, font, max_width: int):
    """先按编号/项目符号拆段，再每段做 wrap_cjk。"""
    paras = _split_bullet_lines(text)
    lines = []
    for p in paras:
        if not p:
            continue
        lines.extend(wrap_cjk(p, font, max_width))
    return lines if lines else [""]


def _draw_multiline(draw, xy, text, font, fill, line_h, max_width):
    """带自动换行的多行文字绘制，返回结束 y。"""
    x, y = xy
    for line in _wrap_text(text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


# ============================================================
# 1. hero_strip — 顶部主视觉条带
# ============================================================
def render_hero_strip(canvas, y, ctx: RenderContext, data: dict) -> int:
    """中央 AI 插画 + 屏幕样式标题卡 + 可选两侧装饰。

    没有 hero_image 时画一个占位（带 'HERO' 字样的低饱和色块），方便联调。

    v0.9.1：如果 brief.canvas.bg_image_path 有值，并且引擎在 _draw_background
    里把 AI 底图按 fit=width 实际占用了 _ai_bg_actual_h 高度，hero_strip 会
    把自己的 band_h 拉到那个高度，让标题卡刚好落在 AI 底图末端。
    """
    draw = ImageDraw.Draw(canvas)
    band_h = data.get("height", 760)
    # 让 hero_strip.height 跟随 AI 底图的实际像素高度（如果有）
    ai_bg_actual_h = ctx.canvas_cfg.get("_ai_bg_actual_h") if hasattr(ctx, "canvas_cfg") else None
    if ai_bg_actual_h and not data.get("height_strict", False):
        band_h = max(band_h, int(ai_bg_actual_h))
    x0, x1 = 0, ctx.width
    y0, y1 = y, y + band_h

    # hero 背景层：AI 插画占位 / 真实图
    hero_img_path = data.get("hero_image")
    if hero_img_path:
        try:
            hero = Image.open(hero_img_path).convert("RGBA")
            ratio = ctx.width / hero.width
            new_h = int(hero.height * ratio)
            hero = hero.resize((ctx.width, new_h), Image.LANCZOS)
            canvas.alpha_composite(hero, (0, y))
            band_h = new_h  # 用真图实际高度
            y1 = y + band_h
        except Exception as e:
            print(f"[warn] hero image 加载失败: {e}")

    # 顶部 logo（默认不渲染；brief 中设置 logo_slot: "horizontal" 等才启用）
    logo_slot = data.get("logo_slot", None)
    logo_size = data.get("logo_height", 56)
    if logo_slot:
        logo = ctx.logo(logo_slot, target_height=logo_size)
        if logo is not None:
            FX.paste_with_shadow(canvas, logo,
                                 (ctx.content_x0, y + 40),
                                 offset=(0, 4), blur=10, alpha=110)

    # 占位装饰：左/右两侧画 PIL 几何小元素，模拟"散点装饰"
    # v0.9.8：占位装饰仅在没有真实 hero_image 时才画。
    # 之前无条件调用导致：即使已经接入 AI 底图，hero 底部仍会被
    # _placeholder_hero_decor 画一条全幅红色横线（line 355-356），
    # 看上去就是"艺术字与下方标题之间总有一条无意义的横线"。
    # 真图就绪后，这些占位元素一律不再画。可由 brief 用
    # hero_strip.placeholder_decor=true 强制开启用于联调。
    if (not hero_img_path) or data.get("placeholder_decor", False):
        _placeholder_hero_decor(canvas, ctx, y, band_h)

    # v0.9.9：可选 hero_mascot —— 把吉祥物 PNG 贴到 hero 右侧/左侧，
    # 与 AI 底图融合。结构：
    # hero_mascot: { image, side: "right"|"left", height_ratio, offset_y, opacity }
    mascot_cfg = data.get("hero_mascot")
    if mascot_cfg and mascot_cfg.get("image"):
        try:
            mp = mascot_cfg["image"]
            if not pathlib.Path(mp).is_absolute():
                mp = str(pathlib.Path(ctx.project_root) / mp) if hasattr(ctx, "project_root") else mp
            m_img = Image.open(mp).convert("RGBA")
            mh = int(band_h * float(mascot_cfg.get("height_ratio", 0.55)))
            mw = int(m_img.width * mh / m_img.height)
            m_img = m_img.resize((mw, mh), Image.LANCZOS)
            side = mascot_cfg.get("side", "right")
            offset_y = int(mascot_cfg.get("offset_y", -40))  # 相对 band 底部
            mx = ctx.width - mw - 40 if side == "right" else 40
            my = y + band_h - mh + offset_y
            opacity = float(mascot_cfg.get("opacity", 1.0))
            if opacity < 1.0:
                a = m_img.split()[-1].point(lambda p: int(p * opacity))
                m_img.putalpha(a)
            # 轻微投影增强立体感
            FX.paste_with_shadow(canvas, m_img, (mx, my),
                                 offset=(0, 10), blur=18, alpha=110)
        except Exception as e:
            print(f"[warn] hero mascot 加载失败: {e}")

    # 标题卡（屏幕样式 / 丝带 / 渐变大字 / AI 艺术字 PNG 图层）
    card = data.get("title_card") or {}
    style = card.get("style", "screen")
    # 标题卡 y 位置 —— 默认放在 hero 下半部
    card_y = y + band_h - card.get("offset_from_bottom", 360)

    # ---- v0.9.4 铁律：艺术字与装饰图的安全区 ----
    # 痛点：AI 装饰图主体常出现在 hero 中上部（hero_visual 重心 y≈band*0.35）。
    #       艺术字若也居中放在中上部，会与主体大面积重叠，盖住主体。
    # 方案：title_card.safe_zone（默认 "bottom"）控制艺术字最低 y：
    #   - "bottom"：艺术字 top 必须 >= y + band_h*0.45（完全在下半部）
    #   - "top"   ：艺术字 bottom 必须 <= y + band_h*0.55（完全在上半部）
    #   - "auto"  ：完全尊重 offset_from_bottom，不约束
    # 这样既允许艺术字与装饰图局部重叠（视觉融合），又保证不完全遮主体。
    safe_zone = (card.get("safe_zone") or "bottom").lower()
    _wordart_bottom = None  # v0.9.9：tight_bottom 用
    if style == "ai_wordart" or style == "image":
        # v0.8 铁律：艺术字必须由 AI 真生成 PNG 图层贴入，本地字体只能兜底
        wa_path = card.get("image") or card.get("wordart_path")
        if wa_path and _resolve_path(wa_path).exists():
            try:
                wa_raw = Image.open(_resolve_path(wa_path))
                # ---- 关键修复：AI 图常常是 RGB 灰底/黑底/白底，直接贴会糊一块矩形 ----
                # 三种触发条件：
                #   1) 模式不是 RGBA（一定要抠）
                #   2) RGBA 但全 alpha=255（API 给了假 alpha）
                #   3) brief 强制 chroma_key=true
                need_key = card.get("chroma_key", "auto")
                if need_key == "auto":
                    if wa_raw.mode != "RGBA":
                        need_key = True
                    else:
                        # 取 alpha 最小值，若 >250 说明根本没抠
                        alpha_min = wa_raw.split()[-1].getextrema()[0]
                        need_key = alpha_min > 250
                if need_key:
                    # bg_kind: brief 显式 > auto
                    bg_kind = card.get("chroma_bg_kind", "auto")
                    # v0.9.1：兼容旧字段。key_lightness/key_saturation/key_softness
                    # 在 dark 模式下当作 darkness_max / saturation_max / softness。
                    wa = FX.chroma_key_to_alpha(
                        wa_raw,
                        bg_lightness_min=card.get("key_lightness_light", 200),
                        bg_darkness_max=card.get("key_lightness", 35) if bg_kind != "light" else 35,
                        bg_saturation_max=card.get("key_saturation", 60),
                        softness=card.get("key_softness", 28),
                        bg_kind=bg_kind,
                        edge_clean=card.get("edge_clean", True),
                    )
                else:
                    wa = wa_raw.convert("RGBA")
                # 可选：用品牌色重染抠出的字（适用 AI 出黑/灰字 + 深底海报场景）
                recolor = card.get("recolor")
                if recolor:
                    fill_a = recolor.get("color_a") or ctx.palette.get("accent_a", "#FFD66B")
                    fill_b = recolor.get("color_b")
                    wa = FX.recolor_with_mask(wa, fill_a, fill_b)
                target_w = int(ctx.width * card.get("width_ratio", 0.86))
                ratio = target_w / wa.width
                target_h = int(wa.height * ratio)
                wa = wa.resize((target_w, target_h), Image.LANCZOS)
                wx = (ctx.width - target_w) // 2
                # ---- v0.9.4 安全区夹紧：避免艺术字完全遮住装饰图主体 ----
                # v0.9.7：艺术字与 hero 底的安全间距从 16 → 4，
                # 让艺术字尽量贴底，下方标题视觉上更紧凑。
                hero_max_y = y + band_h - target_h - 4
                if safe_zone == "bottom":
                    min_y = y + int(band_h * 0.45)
                    if card_y < min_y:
                        card_y = min_y
                    if card_y > hero_max_y:
                        card_y = hero_max_y
                elif safe_zone == "top":
                    max_y = y + int(band_h * 0.55) - target_h
                    if card_y > max_y:
                        card_y = max_y
                    if card_y < y + 16:
                        card_y = y + 16
                else:  # auto：仅夹紧上下边界，不约束相对位置
                    if card_y > hero_max_y:
                        card_y = hero_max_y
                    if card_y < y + 16:
                        card_y = y + 16
                # v0.9.2：浅底 hero（如新春朱红、嘉年华糖果）若再叠 24px 模糊黑阴影，
                # 透明区会被染上一圈灰晕，肉眼像"灰底没抠干净"。允许 brief 关掉/调淡：
                #   shadow=false  → 完全无阴影
                #   shadow={offset,blur,alpha,color} → 自定义
                # 默认仍保留弱阴影（offset=8, blur=14, alpha=70）以保留体积感。
                shadow_cfg = card.get("shadow", "auto")
                if shadow_cfg is False or shadow_cfg == "none":
                    canvas.alpha_composite(wa, (wx, card_y))
                elif isinstance(shadow_cfg, dict):
                    FX.paste_with_shadow(canvas, wa, (wx, card_y),
                                         offset=tuple(shadow_cfg.get("offset", (0, 8))),
                                         blur=int(shadow_cfg.get("blur", 14)),
                                         color=tuple(shadow_cfg.get("color", (0, 0, 0))),
                                         alpha=int(shadow_cfg.get("alpha", 70)))
                else:
                    # auto：浅底走弱阴影、深底走原中等阴影
                    bri = (ctx.canvas_cfg or {}).get("_resolved_brightness") or \
                          getattr(ctx, "brightness", None) or "dark"
                    if bri == "light":
                        FX.paste_with_shadow(canvas, wa, (wx, card_y),
                                             offset=(0, 8), blur=14, alpha=70)
                    else:
                        FX.paste_with_shadow(canvas, wa, (wx, card_y),
                                             offset=(0, 14), blur=24, alpha=140)
                # v0.9.9：记录艺术字真实底（用于 tight_bottom 收缩 band）
                _wordart_bottom = card_y + target_h
            except Exception as e:
                print(f"[warn] AI 艺术字图层加载失败，回退渐变大字: {e}")
                if card.get("lines"):
                    _draw_gradient_title(canvas, ctx, card_y, card["lines"], card)
        elif card.get("lines"):
            print("[warn] ai_wordart 缺 image 路径，回退本地渐变大字")
            _draw_gradient_title(canvas, ctx, card_y, card["lines"], card)
    elif card.get("lines"):
        lines = card["lines"]
        if style == "screen":
            _draw_screen_card(canvas, ctx, card_y, lines)
        elif style == "ribbon":
            _draw_ribbon_card(canvas, ctx, y + band_h - 240, lines)
        elif style == "gradient-large":
            _draw_gradient_title(canvas, ctx, card_y, lines, card)

    subtitle_path = data.get("subtitle_wordart_image") or card.get("subtitle_wordart_image")
    if subtitle_path and _resolve_path(subtitle_path).exists():
        try:
            sub_raw = Image.open(_resolve_path(subtitle_path))
            need_key = card.get("subtitle_chroma_key", card.get("chroma_key", "auto"))
            if need_key == "auto":
                if sub_raw.mode != "RGBA":
                    need_key = True
                else:
                    need_key = sub_raw.split()[-1].getextrema()[0] > 250
            if need_key:
                sub_img = FX.chroma_key_to_alpha(
                    sub_raw,
                    bg_lightness_min=card.get("key_lightness_light", 200),
                    bg_darkness_max=card.get("key_lightness", 35),
                    bg_saturation_max=card.get("key_saturation", 60),
                    softness=card.get("key_softness", 28),
                    bg_kind=card.get("chroma_bg_kind", "auto"),
                    edge_clean=card.get("edge_clean", True),
                )
            else:
                sub_img = sub_raw.convert("RGBA")
            max_w = int(ctx.width * float(card.get("subtitle_width_ratio", 0.72)))
            max_h = int(band_h * float(card.get("subtitle_height_ratio", 0.16)))
            ratio = min(max_w / max(1, sub_img.width), max_h / max(1, sub_img.height), 1.0)
            sw = max(1, int(sub_img.width * ratio))
            sh = max(1, int(sub_img.height * ratio))
            sub_img = sub_img.resize((sw, sh), Image.LANCZOS)
            sx = (ctx.width - sw) // 2
            base_y = (_wordart_bottom + int(card.get("subtitle_gap", 12))) if _wordart_bottom else (y + int(band_h * 0.78))
            sy = min(base_y, y + band_h - sh - 8)
            sy = max(y + 12, sy)
            FX.paste_with_shadow(canvas, sub_img, (sx, int(sy)), offset=(0, 8), blur=14, alpha=70)
            _wordart_bottom = max(_wordart_bottom or 0, int(sy) + sh)
        except Exception as e:
            print(f"[warn] 副标题艺术字图层加载失败: {e}")

    # 整个 hero 区注册为禁飞区（装饰避让）
    ctx.reserve((0, y, ctx.width, y + band_h), pad=0)
    # 🔒 铁律 v0.10.4：tight_bottom — 副标题必须紧贴艺术字底部，视觉间距不超过 1cm（约 38px）。
    # 始终返回 _wordart_bottom + 8px 安全边距，无论艺术字是否超出 band_h。
    # 超出 band_h 时不截断（min 移除），确保副标题跟随艺术字真实位置。
    if data.get("tight_bottom", True) and style in ("ai_wordart", "image") and _wordart_bottom:
        ret_y = int(_wordart_bottom) + 8
        return ret_y
    return y + band_h


def _placeholder_hero_decor(canvas, ctx: RenderContext, y: int, h: int):
    """v0.9.10：彻底关闭占位装饰。

    用户反馈：早期为没真实素材兜底而画的小方块/小三角/小圆点"很丑"，
    且接入真实 AI 装饰图 / hero_mascot 之后这些占位也没必要保留。

    现在策略：直接 return 不画任何东西。
    所有装饰必须由 brief 显式声明（hero_image / hero_mascot / 用户上传的
    icon_path / decor_path），引擎不再凭空臆造。
    """
    return


def _draw_screen_card(canvas, ctx: RenderContext, y: int, lines):
    """黑色屏幕样式标签卡：圆角黑底 + 强阴影 + 渐变描边 + 大字。"""
    cw = int(ctx.content_w * 0.62)
    ch = 220
    x0 = (ctx.width - cw) // 2

    # 主面板（带渐变 + 内高光）
    panel = FX.rounded_panel(
        (cw, ch), fill="#0A0A24", fill_b="#1B1840",
        radius=18, alpha=255,
        border_color=ctx.palette.get("accent_a", "#FBBF24"), border_width=4,
        add_highlight=True,
    )
    # 强阴影抛起
    FX.paste_with_shadow(canvas, panel, (x0, y),
                         offset=(0, 18), blur=30, alpha=170)

    # 标题文字（带外发光）
    f_title = ctx.font(72, role="display")
    n = len(lines)
    line_h = 84
    total_h = n * line_h
    ty = y + (ch - total_h) // 2
    for line in lines:
        bbox = f_title.getbbox(line)
        tw = bbox[2] - bbox[0]
        FX.text_with_glow(
            canvas, (x0 + (cw - tw) // 2, ty),
            line, f_title,
            fill=ctx.palette.get("accent_a", "#FBBF24"),
            glow_color=ctx.palette.get("accent_a", "#FBBF24"),
            glow_blur=14, glow_alpha=200)
        ty += line_h


def _draw_ribbon_card(canvas, ctx: RenderContext, y: int, lines):
    """黄色丝带：黄底渐变 + 内高光 + 黑字 + 黑色描边 + 投影。"""
    cw = int(ctx.content_w * 0.7)
    ch = 160 if len(lines) <= 1 else 220
    x0 = (ctx.width - cw) // 2
    accent_a = ctx.palette.get("accent_a", "#FBBF24")
    # 渐变黄
    panel = FX.rounded_panel(
        (cw, ch), fill="#FFD66B", fill_b=accent_a,
        radius=18, border_color="#0E0F1A", border_width=5,
        add_highlight=True)
    FX.paste_with_shadow(canvas, panel, (x0, y),
                         offset=(0, 14), blur=24, alpha=140)
    f = ctx.font(72, role="display")
    text = " ".join(lines)
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ImageDraw.Draw(canvas).text(
        (x0 + (cw - tw) // 2, y + (ch - th) // 2 - 10),
        text, font=f, fill="#0E0F1A",
        stroke_width=2, stroke_fill="#000000")


def _draw_gradient_title(canvas, ctx: RenderContext, y: int, lines, card):
    """大字渐变标题（无卡片底，纯发光大字 + 副标 + logo emblem）。"""
    color_a = card.get("color_a") or ctx.palette.get("accent_a", "#FFD66B")
    color_b = card.get("color_b") or ctx.palette.get("accent_b", "#FF6B6B")
    f_main = ctx.font(card.get("size", 110), role="display")

    cy = y
    for line in lines:
        bbox = f_main.getbbox(line)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # 先打外发光（绘制白色到底层 + 模糊）
        glow = Image.new("RGBA", (tw + 80, th + 80), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.text((40 - bbox[0], 40 - bbox[1]), line, font=f_main, fill=(255, 255, 255, 200))
        glow = glow.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(
            glow, ((ctx.width - tw) // 2 - 40, cy - 40))
        # 渐变填充字
        FX.text_with_gradient(
            canvas, ((ctx.width - tw) // 2, cy),
            line, f_main, color_a=color_a, color_b=color_b,
            stroke_width=4, stroke_fill="#0E0F1A")
        cy += th + 30


# ============================================================
# 2. lead_paragraph — 欢迎语段落
# ============================================================
def render_lead_paragraph(canvas, y, ctx: RenderContext, data: dict) -> int:
    text = data.get("text", "")
    style = data.get("panel_style", "frosted")
    asset_frame_path = data.get("asset_frame_path", "")
    font_size = int(data.get("font_size", 38))
    font_role = data.get("font_role", "body")
    f = ctx.font(font_size, role=font_role)
    line_h = int(data.get("line_height", max(44, font_size + 22)))
    pad = int(data.get("pad", 36))
    max_text_w = ctx.content_w - pad * 2
    lines = _wrap_text_block(text, f, max_text_w)
    panel_h = pad * 2 + line_h * len(lines)

    if style == "asset_frame" and asset_frame_path:
        try:
            _draw_asset_frame(canvas, ctx.content_x0, y, ctx.content_w, panel_h,
                              asset_frame_path, corner=60)
        except Exception:
            _frosted_panel(canvas, (ctx.content_x0, y, ctx.content_x1, y + panel_h),
                           radius=20, alpha=200)
        draw = ImageDraw.Draw(canvas)
        f_body = f
        cy = y + pad
        lead_text_color = data.get("text_color") or "#2D0B5C"
        if lead_text_color == "auto":
            lead_text_color = "#2D0B5C"
        for line in lines:
            draw.text((ctx.content_x0 + pad, cy), line, font=f_body, fill=lead_text_color)
            cy += line_h
        ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
        return y + panel_h

    if style == "none":
        # 无框：直接在底色上渲染文字，不画任何背景面板
        draw = ImageDraw.Draw(canvas)
        font_role = data.get("font_role", "body")  # body=W3 / display=W7
        f_body = ctx.font(int(data.get("font_size", 38)), role=font_role)
        lead_text_color = data.get("text_color", "#E8D8FF")
        # 重新按实际字号和 pad 计算
        actual_pad = int(data.get("pad", pad))
        actual_line_h = int(data.get("line_height", line_h))
        max_text_w2 = ctx.content_w - actual_pad * 2
        lines2 = _wrap_text_block(text, f_body, max_text_w2)
        cy = y + actual_pad
        for line in lines2:
            draw.text((ctx.content_x0 + actual_pad, cy), line, font=f_body, fill=lead_text_color)
            cy += actual_line_h
        total_h = actual_pad + actual_line_h * len(lines2) + actual_pad
        return y + total_h

    if style == "yellow-card":
        accent_a = ctx.palette.get("accent_a", "#FBBF24")
        panel = FX.rounded_panel(
            (ctx.content_w, panel_h),
            fill="#FFD66B", fill_b=accent_a,
            radius=20, add_highlight=True,
            border_color="#0E0F1A", border_width=3)
        FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                             offset=(0, 12), blur=22, alpha=130)
        text_color = _text_on(ctx, "accent_a", fallback_bg=accent_a)
        stroke = None
    else:
        # v0.9.3 铁律：浅底配色统一走"米白底 + 深字"，不再硬写深底白字
        # v0.9.10：light 模式 alpha 从 235 → 255（全不透明），避免底图渐变
        # （米白→朱红）从 panel 背后透出，导致下方 panel 视觉发灰发暗。
        panel_fill, text_color = _panel_pair(ctx)
        is_light = _brightness(ctx) == "light"
        panel = FX.rounded_panel(
            (ctx.content_w, panel_h), fill=panel_fill,
            radius=20, alpha=255 if is_light else 220,
            add_highlight=False,
            border_color=ctx.palette.get("accent_a", "#FBBF24"),
            border_width=2)
        FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                             offset=(0, 8), blur=20, alpha=60 if is_light else 80)
        stroke = None
    if data.get("text_color") and data.get("text_color") != "auto":
        text_color = data.get("text_color")
    draw = ImageDraw.Draw(canvas)
    cy = y + pad
    # v0.9.10：W7 标题字 + W3 正文字的差异化。lead_paragraph 走 W3 + 伪粗。
    f_body = f
    explicit_text_color = data.get("text_color")
    if explicit_text_color and explicit_text_color != "auto":
        text_color = explicit_text_color
    body_kw = ctx.body_text_kwargs(fill=text_color)
    for line in lines:
        draw.text((ctx.content_x0 + pad, cy), line, font=f_body, **body_kw)
        cy += line_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ============================================================
# 3. section_title_bar — 段落分隔块标题
# ============================================================
def render_section_title_bar(canvas, y, ctx: RenderContext, data: dict) -> int:
    text = data.get("text", "")
    style = data.get("style", "plain")
    f = ctx.font(56, role="display")
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bar_h = 130
    bar_w = max(tw + 240, 560)
    x0 = (ctx.width - bar_w) // 2
    accent_a = ctx.palette.get("accent_a", "#FBBF24")
    accent_b = ctx.palette.get("accent_b", "#A78BFA")

    if style == "numbered":
        # 半透明大数字 + 标题 + 装饰横线（去框）
        index = data.get("index", 0)
        accent_color = data.get("accent_color") or accent_a
        f_num = ctx.font(140, role="display")
        f_title = ctx.font(56, role="display")
        num_text = str(index) if index else "·"
        # 估宽：数字（半透明）+ 标题
        nbox = f_num.getbbox(num_text)
        nw, nh = nbox[2] - nbox[0], nbox[3] - nbox[1]
        tbox = f_title.getbbox(text)
        ttw, tth = tbox[2] - tbox[0], tbox[3] - tbox[1]
        title_y = y + 8  # v0.9.9：原 +30，下移过多，与 hero 形成断层；改为 +8 紧凑
        # 数字（半透明，放在标题左侧偏上）
        big = Image.new("RGBA", (nw + 40, nh + 40), (0, 0, 0, 0))
        ImageDraw.Draw(big).text((20 - nbox[0], 20 - nbox[1]), num_text,
                                 font=f_num,
                                 fill=(*hex_to_rgb(accent_color), 80))
        # 直接贴
        canvas.alpha_composite(big, (ctx.content_x0 - 10, title_y - 30))
        # 标题（在数字右侧）
        d = ImageDraw.Draw(canvas)
        title_x = ctx.content_x0 + nw + 8
        # v0.9.3：light 模式标题用深字（不再写死白），dark 模式仍白
        title_fill = ctx.palette.get("text_on_dark", "#1F2937") if _brightness(ctx) == "light" else "#FFFFFF"
        if _brightness(ctx) == "light" and title_fill.upper() in ("#FFFFFF", "#FFF7ED", "#FFF8EE"):
            title_fill = "#1F2937"
        d.text((title_x, title_y + (nh - tth) // 2), text,
               font=f_title, fill=title_fill)
        # v0.9.7：装饰横线默认关掉（用户反馈：艺术字下方"中间总有一条线"，
        # 让 hero→title 之间多了一道无意义的视觉切线）。
        # 仅当 brief 显式给 show_underline=true 才画。
        if data.get("show_underline", False):
            line_y = title_y + nh + 8
            d.line([(title_x, line_y),
                    (title_x + max(ttw, 200), line_y)],
                   fill=accent_color, width=4)
        # v0.9.10：标题→正文间距硬约束。
        # 历史问题：bar_h = nh + 50 留 42px 空白 + 外层再叠 14px TITLE_TO_BODY_GAP
        # = 标题底到下一段正文有 56px 空气，看起来"标题游离"。
        # 现改为 bar_h = nh + 18，即标题底到 return y 只有 ~10px，
        # 下游一律不再加 TITLE_TO_BODY_GAP，把"小标题→正文间距"
        # 锁死成全局固定 ~10px。
        bar_h = nh + 18
        ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + bar_h))
        return y + bar_h

    if style == "plain":
        # 简洁标题：文字 + 可配置下划线，默认跟随整体 accent 色
        f_plain = ctx.font(int(data.get("font_size", 52)), role=data.get("font_role", "display"))
        bbox_p = f_plain.getbbox(text)
        tw_p, th_p = bbox_p[2] - bbox_p[0], bbox_p[3] - bbox_p[1]
        tx = (ctx.width - tw_p) // 2
        ty = y + 20

        # 文字阴影层（向右下偏移2px，纯黑半透明）
        shadow_layer = Image.new("RGBA", (ctx.width, th_p + 20), (0, 0, 0, 0))
        shadow_d = ImageDraw.Draw(shadow_layer)
        shadow_d.text((tx - bbox_p[0] + 3, 10 - bbox_p[1] + 3), text, font=f_plain,
                      fill=(0, 0, 0, 160))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(4))
        canvas.alpha_composite(shadow_layer, (0, ty - 10))

        title_color = data.get("text_color") or "#FFFFFF"
        if title_color == "auto":
            title_color = "#FFFFFF"
        ImageDraw.Draw(canvas).text((tx - bbox_p[0], ty - bbox_p[1]), text,
                                    font=f_plain, fill=title_color)

        deco_path = data.get("decoration_path") or data.get("title_decoration_path")
        if deco_path:
            try:
                deco_size = int(data.get("decoration_size") or data.get("title_decoration_size") or 42)
                deco = Image.open(_resolve_path(deco_path)).convert("RGBA")
                deco.thumbnail((deco_size, deco_size), Image.LANCZOS)
                pos = data.get("decoration_position") or "left"
                gap = int(data.get("decoration_gap") or 18)
                if pos == "right":
                    dx = tx + tw_p + gap
                else:
                    dx = tx - gap - deco.width
                dx = max(ctx.content_x0, min(dx, ctx.content_x1 - deco.width))
                dy = ty + max(0, (th_p - deco.height) // 2)
                canvas.alpha_composite(deco, (dx, dy))
            except Exception as e:
                print(f"[warn] section title decoration failed: {e}")

        underline_color = data.get("underline_color") or accent_a
        if underline_color == "auto":
            underline_color = accent_a
        ul_w = tw_p + 60
        ul_x0 = (ctx.width - ul_w) // 2
        ul_y = ty + th_p + 12
        ul_img = Image.new("RGBA", (ul_w, 4), (0, 0, 0, 0))
        ur, ug, ub = hex_to_rgb(underline_color)
        for xi in range(ul_w):
            ul_img.putpixel((xi, 0), (ur, ug, ub, 180))
            ul_img.putpixel((xi, 1), (ur, ug, ub, 255))
            ul_img.putpixel((xi, 2), (ur, ug, ub, 255))
            ul_img.putpixel((xi, 3), (ur, ug, ub, 170))
        canvas.alpha_composite(ul_img, (ul_x0, ul_y))

        bar_h = (ul_y - y) + 4 + 32   # 下划线底 + 32px 到正文的间距
        ctx.reserve((0, y, ctx.width, y + bar_h))
        return y + bar_h

    if style == "neon":
        # 渐变描边光圈 + 半透明黑底 + 文字外发光
        panel = FX.rounded_panel(
            (bar_w, bar_h), fill="#0A0A24", fill_b="#1B1840",
            radius=18, alpha=200,
            border_color=accent_a, border_width=4, add_highlight=True)
        # 模糊外发光
        glow = Image.new("RGBA", (bar_w + 80, bar_h + 80), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle(
            [40, 40, bar_w + 40, bar_h + 40], radius=18,
            fill=(*hex_to_rgb(accent_a), 110))
        glow = glow.filter(ImageFilter.GaussianBlur(20))
        canvas.alpha_composite(glow, (x0 - 40, y - 40))
        canvas.alpha_composite(panel, (x0, y))
        # 两侧装饰小三角（保留）
        td = ImageDraw.Draw(canvas)
        td.polygon([(x0 + 28, y + bar_h // 2), (x0 + 60, y + bar_h // 2 - 18),
                    (x0 + 60, y + bar_h // 2 + 18)], fill=accent_a)
        td.polygon([(x0 + bar_w - 28, y + bar_h // 2), (x0 + bar_w - 60, y + bar_h // 2 - 18),
                    (x0 + bar_w - 60, y + bar_h // 2 + 18)], fill=accent_a)
        # 文字外发光
        FX.text_with_glow(
            canvas, (x0 + (bar_w - tw) // 2, y + (bar_h - th) // 2 - 8),
            text, f, fill=accent_a, glow_color=accent_a,
            glow_blur=10, glow_alpha=180)
    elif style == "ribbon":
        panel = FX.rounded_panel(
            (bar_w, bar_h), fill="#FFD66B", fill_b=accent_a,
            radius=18, border_color="#0E0F1A", border_width=5,
            add_highlight=True)
        FX.paste_with_shadow(canvas, panel, (x0, y),
                             offset=(0, 12), blur=20, alpha=130)
        # v0.6: 黄底已极亮，黑字去描边
        ImageDraw.Draw(canvas).text(
            (x0 + (bar_w - tw) // 2, y + (bar_h - th) // 2 - 8),
            text, font=f, fill="#0E0F1A")
    else:  # screen
        panel = FX.rounded_panel(
            (bar_w, bar_h), fill="#0A0A24", fill_b="#1B1840",
            radius=14, alpha=230, add_highlight=True)
        FX.paste_with_shadow(canvas, panel, (x0, y),
                             offset=(0, 10), blur=18, alpha=120)
        ImageDraw.Draw(canvas).text(
            (x0 + (bar_w - tw) // 2, y + (bar_h - th) // 2 - 8),
            text, font=f, fill=_text_on(ctx, "dark", fallback_bg="#0A0A24"))
    ctx.reserve((x0, y, x0 + bar_w, y + bar_h))
    return y + bar_h


# ============================================================
# 4. info_card — H 标 + 段落
# ============================================================
def render_info_card(canvas, y, ctx: RenderContext, data: dict) -> int:
    """v0.9: 支持两种入口
       A) heading + body 经典模式
       B) 仅 bullets （无 heading） —— 编号每条另起一行的"你将获得"形态
    """
    heading = data.get("heading", "")
    body = data.get("body", "")
    bullets = data.get("bullets") or []
    panel_style = data.get("panel_style", "frosted")
    asset_frame_path = data.get("asset_frame_path", "")

    # ---- v0.9 模式 B：bullets 优先（无 heading） ----
    if bullets and not heading:
        return render_bullet_points_block(canvas, y, ctx, {
            "bullets": bullets,
            "number_style": data.get("number_style", "circle"),
        })

    # ======= asset_frame 模式：整卡用素材框背景 =======
    if panel_style == "asset_frame" and asset_frame_path:
        fh = ctx.font(44, role="display")
        fb = ctx.font(32, role="body")
        PAD_X, PAD_Y = 40, 30
        LINE_H = 52
        logo_path = data.get("logo_path", "")
        logo_height = int(data.get("logo_height", 80))

        # 加载 logo（如有），并反色为白色（用于深色框）
        logo_img = None
        logo_w = 0
        if logo_path:
            try:
                _logo_raw = Image.open(logo_path).convert("RGBA")
                _logo_ratio = logo_height / _logo_raw.height
                logo_w = int(_logo_raw.width * _logo_ratio)
                _logo_resized = _logo_raw.resize((logo_w, logo_height), Image.LANCZOS)
                # 反色：黑色像素→白色（深色框里黑 logo 不可见，需要反色）
                if data.get("logo_invert", True):
                    r, g, b, a = _logo_resized.split()
                    r = r.point(lambda x: 255 - x)
                    g = g.point(lambda x: 255 - x)
                    b = b.point(lambda x: 255 - x)
                    logo_img = Image.merge("RGBA", (r, g, b, a))
                else:
                    logo_img = _logo_resized
            except Exception as e:
                print(f"[warn] logo 加载失败: {e}")

        # 文字区宽度：有 logo 时留出 logo + gap 空间
        LOGO_GAP = 40
        text_x_offset = PAD_X + (logo_w + LOGO_GAP if logo_img else 0)
        max_text_w = ctx.content_w - text_x_offset - PAD_X

        body_lines = _wrap_text_block(body, fb, max_text_w) if body else []
        hbox_tmp = fh.getbbox(heading) if heading else (0, 0, 0, 0)
        heading_h = (hbox_tmp[3] - hbox_tmp[1] + PAD_Y) if heading else 0
        body_h = LINE_H * len(body_lines) + PAD_Y if body_lines else 0
        content_h = PAD_Y + heading_h + body_h + PAD_Y
        # logo 存在时保证卡片足够高
        if logo_img:
            content_h = max(content_h, PAD_Y * 2 + logo_height + PAD_Y)
        total_h = max(content_h, 100)

        try:
            _draw_asset_frame(canvas, ctx.content_x0, y, ctx.content_w, total_h,
                              asset_frame_path, corner=60)
        except Exception:
            _frosted_panel(canvas, (ctx.content_x0, y, ctx.content_x1, y + total_h),
                           radius=20, alpha=200)

        # 文字颜色：深框用白色，浅框用深紫色（brief 可用 text_color 覆盖）
        TEXT_COLOR = data.get("text_color", "#FFFFFF")
        d = ImageDraw.Draw(canvas)

        # 贴 logo（垂直居中）
        if logo_img:
            logo_y = y + (total_h - logo_height) // 2
            logo_x = ctx.content_x0 + PAD_X
            if canvas.mode == "RGBA":
                canvas.alpha_composite(logo_img, (logo_x, logo_y))
            else:
                tmp_c = canvas.convert("RGBA")
                tmp_c.alpha_composite(logo_img, (logo_x, logo_y))
                canvas.paste(tmp_c.convert("RGB"), (0, 0))

        cy = y + PAD_Y
        if heading:
            hbox = fh.getbbox(heading)
            d.text((ctx.content_x0 + text_x_offset, cy - hbox[1]), heading, font=fh,
                   fill=TEXT_COLOR)
            cy += hbox[3] - hbox[1] + PAD_Y // 2
        for line in body_lines:
            d.text((ctx.content_x0 + text_x_offset, cy), line, font=fb, fill=TEXT_COLOR)
            cy += LINE_H

        ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
        return y + total_h

    # ======= 原有逻辑 =======
    # heading 块（渐变 + 阴影 + 内高光）
    fh = ctx.font(48, role="display")
    hbox = fh.getbbox(heading)
    hw, hh = hbox[2] - hbox[0], hbox[3] - hbox[1]
    h_pad_x, h_pad_y = 32, 18
    h_panel_w = hw + h_pad_x * 2
    h_panel_h = hh + h_pad_y * 2 + 8
    primary = ctx.palette.get("primary", "#3B82F6")
    accent_b = ctx.palette.get("accent_b", "#A78BFA")
    h_panel = FX.rounded_panel(
        (h_panel_w, h_panel_h), fill=primary, fill_b=accent_b,
        radius=12, direction="horizontal", add_highlight=True)
    FX.paste_with_shadow(canvas, h_panel, (ctx.content_x0, y),
                         offset=(0, 10), blur=18, alpha=120)
    head_color = _text_on(ctx, "primary", fallback_bg=primary)
    # v0.6: heading 是大字，渐变底已有空间感；只在与 primary 对比不足时才描边
    ImageDraw.Draw(canvas).text(
        (ctx.content_x0 + h_pad_x, y + h_pad_y), heading, font=fh, fill=head_color)

    body_y = y + h_panel_h + 18

    # v0.6: body 用深色实底面板 + 白字（不再 stroke）
    fb = ctx.font(32)
    line_h = 52
    pad = 30
    max_text_w = ctx.content_w - pad * 2
    lines = _wrap_text_block(body, fb, max_text_w)
    panel_h = pad * 2 + line_h * len(lines)
    panel_fill, _ptext = _panel_pair(ctx)
    if data.get("text_color") and data.get("text_color") != "auto":
        _ptext = data.get("text_color")
    body_panel = FX.rounded_panel(
        (ctx.content_w, panel_h), fill=panel_fill,
        radius=18, alpha=_panel_alpha(ctx, 215), add_highlight=False,
        border_color=ctx.palette.get("accent_a", "#FBBF24"),
        border_width=2)
    FX.paste_with_shadow(canvas, body_panel, (ctx.content_x0, body_y),
                         offset=(0, 8), blur=20, alpha=80)
    draw = ImageDraw.Draw(canvas)
    body_color = _ptext
    cy = body_y + pad
    for line in lines:
        draw.text((ctx.content_x0 + pad, cy), line, font=fb, fill=body_color)
        cy += line_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, body_y + panel_h))
    return body_y + panel_h


# ============================================================
# 5. info_card_with_qr — info_card + 右侧二维码 / 报名按钮
# ============================================================
def render_info_card_with_qr(canvas, y, ctx: RenderContext, data: dict) -> int:
    """v0.9.7：右侧支持两种 CTA 模式：
       cta_mode = "qr"     → 二维码（默认，原行为）
       cta_mode = "button" → 圆角按钮占位 + 提示文字（用户后期人工挂链接）
    button_text  : 按钮主标，默认 "立即报名"
    button_hint  : 按钮下方小字，默认 "扫码或点击跳转"
    """
    heading = data.get("heading", "")
    body = data.get("body", "")
    qr_path = data.get("qr_image")
    qr_label = data.get("qr_label", "二维码")
    cta_mode = (data.get("cta_mode") or "qr").lower()
    button_text = data.get("button_text", "立即报名")
    button_hint = data.get("button_hint", "海报发布后将挂上报名链接")

    # heading 块（同 info_card）
    fh = ctx.font(48)
    hbox = fh.getbbox(heading)
    hw, hh = hbox[2] - hbox[0], hbox[3] - hbox[1]
    h_pad_x, h_pad_y = 32, 18
    h_panel_w = hw + h_pad_x * 2
    h_panel_h = hh + h_pad_y * 2 + 8
    primary = ctx.palette.get("primary", "#3B82F6")
    accent_a = ctx.palette.get("accent_a", "#FBBF24")
    h_panel = Image.new("RGBA", (h_panel_w, h_panel_h), (0, 0, 0, 0))
    ImageDraw.Draw(h_panel).rounded_rectangle(
        [0, 0, h_panel_w, h_panel_h], radius=12,
        fill=primary)
    canvas.alpha_composite(h_panel, (ctx.content_x0, y))
    head_color = _text_on(ctx, "primary", fallback_bg=primary)
    ImageDraw.Draw(canvas).text(
        (ctx.content_x0 + h_pad_x, y + h_pad_y), heading, font=fh, fill=head_color)

    body_y = y + h_panel_h + 16

    # ---- 右侧 CTA 列宽 ----
    if cta_mode == "button":
        cta_col_w = 320            # 按钮列比 QR 略宽，承载提示文字
    else:
        cta_col_w = 260
    text_x1 = ctx.content_x1 - cta_col_w - 24

    # body
    fb = ctx.font(34, role="display")
    line_h = 56
    pad = 30
    max_text_w = (text_x1 - ctx.content_x0) - pad * 2
    lines = _wrap_text(body, fb, max_text_w)
    text_panel_h = pad * 2 + line_h * len(lines)

    if cta_mode == "button":
        cta_block_h = 280  # 按钮 110 + 提示 ~ 80 + padding
    else:
        cta_block_h = 200 + 50  # QR 200 + label
    panel_h = max(text_panel_h, cta_block_h + pad * 2)

    panel_fill, _ptext = _panel_pair(ctx)
    _frosted_panel(canvas, (ctx.content_x0, body_y, ctx.content_x1, body_y + panel_h),
                   radius=18, alpha=_panel_alpha(ctx, 215), fill_hex=panel_fill)
    draw = ImageDraw.Draw(canvas)
    body_color = _ptext
    cy = body_y + pad
    for line in lines:
        draw.text((ctx.content_x0 + pad, cy), line, font=fb, fill=body_color)
        cy += line_h

    if cta_mode == "button":
        # ---- 按钮 CTA：圆角渐变按钮 + 下方两行小提示 ----
        btn_w = cta_col_w - 24
        btn_h = 110
        btn_x = ctx.content_x1 - cta_col_w + 12
        btn_y = body_y + (panel_h - cta_block_h) // 2
        # 渐变按钮
        btn_panel = FX.rounded_panel(
            (btn_w, btn_h), fill="#FFD66B", fill_b=accent_a,
            radius=55, border_color="#0E0F1A", border_width=4,
            add_highlight=True)
        FX.paste_with_shadow(canvas, btn_panel, (btn_x, btn_y),
                             offset=(0, 10), blur=18, alpha=130)
        f_btn = ctx.font(40, role="display")
        bbb = f_btn.getbbox(button_text)
        btw, bth = bbb[2] - bbb[0], bbb[3] - bbb[1]
        draw.text((btn_x + (btn_w - btw) // 2 - bbb[0],
                   btn_y + (btn_h - bth) // 2 - bbb[1]),
                  button_text, font=f_btn, fill="#0E0F1A")
        # 按钮下方提示（W3 小字 + 自动换行）
        f_hint = ctx.font(22)
        hint_lines = wrap_cjk(button_hint, f_hint, btn_w + 8)
        hy = btn_y + btn_h + 18
        for ln in hint_lines:
            hbb = f_hint.getbbox(ln)
            hw_ = hbb[2] - hbb[0]
            draw.text((btn_x + (btn_w - hw_) // 2 - hbb[0], hy),
                      ln, font=f_hint, fill=body_color)
            hy += 32
    else:
        # ---- 二维码 CTA：原逻辑 ----
        qr_size = 200
        qr_x = ctx.content_x1 - cta_col_w + (cta_col_w - qr_size) // 2
        qr_y = body_y + (panel_h - qr_size - 50) // 2
        qr_bg = Image.new("RGBA", (qr_size + 16, qr_size + 16), (255, 255, 255, 255))
        canvas.alpha_composite(qr_bg, (qr_x - 8, qr_y - 8))
        if qr_path:
            try:
                qr = Image.open(qr_path).convert("RGBA").resize((qr_size, qr_size), Image.LANCZOS)
                canvas.alpha_composite(qr, (qr_x, qr_y))
            except Exception:
                ImageDraw.Draw(canvas).rectangle(
                    [qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], fill="#222222")
        else:
            d2 = ImageDraw.Draw(canvas)
            cell = qr_size // 10
            for i in range(10):
                for j in range(10):
                    if (i + j) % 2 == 0:
                        d2.rectangle([qr_x + i * cell, qr_y + j * cell,
                                      qr_x + (i + 1) * cell, qr_y + (j + 1) * cell], fill="#0E0F1A")
        fl = ctx.font(26)
        lbox = fl.getbbox(qr_label)
        lw = lbox[2] - lbox[0]
        ImageDraw.Draw(canvas).text(
            (qr_x + (qr_size - lw) // 2, qr_y + qr_size + 14),
            qr_label, font=fl, fill=body_color)

    ctx.reserve((ctx.content_x0, y, ctx.content_x1, body_y + panel_h))
    return body_y + panel_h


# ============================================================
# 6. qa_block — 问答列表
# ============================================================
def render_qa_block(canvas, y, ctx: RenderContext, data: dict) -> int:
    items = data.get("items", [])
    fq = ctx.font(36)
    fa = ctx.font(28)
    q_color = ctx.palette.get("accent_a", "#FBBF24")
    a_color = _ptext
    line_h_q = 54
    line_h_a = 46
    item_gap = 28
    pad = 36
    inner_pad = 20
    max_w = ctx.content_w - pad * 2 - inner_pad * 2

    # v0.6: 先估算面板高度
    total_h = pad * 2
    cached = []
    for it in items:
        q_lines = _wrap_text(it.get("q", ""), fq, max_w)
        a_lines = _wrap_text(it.get("a", ""), fa, max_w)
        block_h = line_h_q * len(q_lines) + 8 + line_h_a * len(a_lines)
        cached.append((q_lines, a_lines, block_h))
        total_h += block_h + item_gap
    total_h -= item_gap if items else 0

    # 深底面板
    panel_fill, _ptext = _panel_pair(ctx)
    panel = FX.rounded_panel(
        (ctx.content_w, total_h), fill=panel_fill,
        radius=18, alpha=_panel_alpha(ctx, 215), add_highlight=False,
        border_color=ctx.palette.get("accent_a", "#FBBF24"),
        border_width=2)
    FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                         offset=(0, 8), blur=20, alpha=80)

    cur_y = y + pad
    d = ImageDraw.Draw(canvas)
    for q_lines, a_lines, _ in cached:
        for line in q_lines:
            d.text((ctx.content_x0 + pad, cur_y), line, font=fq, fill=q_color)
            cur_y += line_h_q
        cur_y += 8
        for line in a_lines:
            d.text((ctx.content_x0 + pad, cur_y), line, font=fa, fill=a_color)
            cur_y += line_h_a
        cur_y += item_gap
    cur_y = y + total_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, cur_y))
    return cur_y


# ============================================================
# 7. meta_row — 横排关键信息
# ============================================================
def render_meta_row(canvas, y, ctx: RenderContext, data: dict) -> int:
    """v0.9.1 measure-first 修复：label / value 都做 wrap_cjk，cell_h 由内容决定，
    避免长 value 直接糊到边缘。字号在 1200 宽下保持可读，自动按列数缩档。"""
    items = data.get("items", [])
    if not items:
        return y
    n = len(items)
    gap = 24
    cell_w = (ctx.content_w - gap * (n - 1)) // n
    # 字号档位：3 列默认 36/22；4 列降到 32/20
    if n >= 4:
        f_value_size, f_label_size = 30, 20
    elif n == 3:
        f_value_size, f_label_size = 36, 22
    else:
        f_value_size, f_label_size = 42, 24
    fl = ctx.font(f_label_size)
    fv = ctx.font(f_value_size, role="display")
    pad_x, pad_y = 22, 22
    label_line_h = f_label_size + 8
    value_line_h = f_value_size + 12

    # measure first
    cells = []
    cell_text_w = cell_w - pad_x * 2
    for it in items:
        label = it.get("label", "")
        value = it.get("value", "")
        l_lines = wrap_cjk(label, fl, cell_text_w) if label else []
        v_lines = wrap_cjk(value, fv, cell_text_w) if value else []
        h = pad_y * 2 + len(l_lines) * label_line_h + 8 + len(v_lines) * value_line_h
        cells.append({"label_lines": l_lines, "value_lines": v_lines, "h": h})
    cell_h = max(c["h"] for c in cells)
    cell_h = max(cell_h, 140)

    accent_a = ctx.palette.get("accent_a", "#FBBF24")
    for i, c in enumerate(cells):
        x0 = ctx.content_x0 + i * (cell_w + gap)
        panel = FX.rounded_panel(
            (cell_w, cell_h), fill="#FFD66B", fill_b=accent_a,
            radius=18, border_color="#0E0F1A", border_width=2,
            add_highlight=True)
        FX.paste_with_shadow(canvas, panel, (x0, y),
                             offset=(0, 10), blur=18, alpha=120)
        d = ImageDraw.Draw(canvas)
        meta_text = _text_on(ctx, "accent_a", fallback_bg=accent_a)
        ty = y + pad_y
        for ln in c["label_lines"]:
            d.text((x0 + pad_x, ty), ln, font=fl, fill=meta_text)
            ty += label_line_h
        ty += 6
        for ln in c["value_lines"]:
            d.text((x0 + pad_x, ty), ln, font=fv, fill=meta_text)
            ty += value_line_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + cell_h))
    return y + cell_h


# ============================================================
# 8. schedule_table — 课程表
# ============================================================
def render_schedule_table(canvas, y, ctx: RenderContext, data: dict) -> int:
    columns = data.get("columns", [])
    rows = data.get("rows", [])
    if not columns:
        return y
    fh = ctx.font(28)
    fr = ctx.font(26)
    n_col = len(columns)
    col_w = ctx.content_w // n_col
    row_h = 70
    head_h = 80
    table_h = head_h + row_h * len(rows)
    primary = ctx.palette.get("primary", "#3B82F6")
    head_color = _text_on(ctx, "primary", fallback_bg=primary)
    row_color = _text_on(ctx, "dark", fallback_bg=ctx.bg_base_color)
    row_halo = _halo(row_color)
    panel_fill, _ptext = _panel_pair(ctx)
    # 表头
    head = Image.new("RGBA", (ctx.content_w, head_h), (0, 0, 0, 0))
    ImageDraw.Draw(head).rounded_rectangle(
        [0, 0, ctx.content_w, head_h], radius=14,
        fill=primary)
    canvas.alpha_composite(head, (ctx.content_x0, y))
    d = ImageDraw.Draw(canvas)
    for i, c in enumerate(columns):
        bbox = fh.getbbox(c)
        tw = bbox[2] - bbox[0]
        d.text((ctx.content_x0 + i * col_w + (col_w - tw) // 2, y + 24),
               c, font=fh, fill=head_color)
    # 行
    for ri, row in enumerate(rows):
        ry = y + head_h + ri * row_h
        # v0.6: 行底统一深色磨砂 alpha=_panel_alpha(ctx, 180)，奇偶交替深浅
        row_alpha = 180 if ri % 2 == 0 else 120
        _frosted_panel(canvas,
                       (ctx.content_x0, ry, ctx.content_x1, ry + row_h),
                       radius=0, alpha=row_alpha,
                       fill_hex=panel_fill)
        for ci, val in enumerate(row[:n_col]):
            txt = str(val)
            bbox = fr.getbbox(txt)
            tw = bbox[2] - bbox[0]
            d.text((ctx.content_x0 + ci * col_w + (col_w - tw) // 2, ry + 18),
                   txt, font=fr, fill=_ptext)
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + table_h))
    return y + table_h


# ============================================================
# 9. resource_grid — 圆形头像网格
# ============================================================
def render_resource_grid(canvas, y, ctx: RenderContext, data: dict) -> int:
    items = data.get("items", [])
    cols = data.get("cols", 4)
    if not items:
        return y
    avatar_size = 140
    gap_x = (ctx.content_w - cols * avatar_size) // max(cols - 1, 1) if cols > 1 else 0
    rows_n = (len(items) + cols - 1) // cols
    cell_h = avatar_size + 64  # 头像 + 文字
    fn = ctx.font(26)
    for idx, item in enumerate(items):
        ri, ci = divmod(idx, cols)
        cx = ctx.content_x0 + ci * (avatar_size + gap_x) + avatar_size // 2
        cy = y + ri * cell_h + avatar_size // 2
        # 圆底（占位）
        d = ImageDraw.Draw(canvas)
        d.ellipse([cx - avatar_size // 2, cy - avatar_size // 2,
                   cx + avatar_size // 2, cy + avatar_size // 2],
                  fill=ctx.palette.get("primary", "#3B82F6"),
                  outline=ctx.palette.get("accent_a", "#FBBF24"), width=4)
        avatar_path = item.get("avatar")
        if avatar_path:
            try:
                av = Image.open(avatar_path).convert("RGBA").resize(
                    (avatar_size - 12, avatar_size - 12), Image.LANCZOS)
                # 圆形遮罩
                mask = Image.new("L", av.size, 0)
                ImageDraw.Draw(mask).ellipse([0, 0, av.size[0], av.size[1]], fill=255)
                canvas.paste(av, (cx - av.size[0] // 2, cy - av.size[1] // 2), mask)
            except Exception:
                pass
        # 名字 —— v0.6: chip 底框替代描边
        name = item.get("name", "")
        if name:
            _pf, _pt = _panel_pair(ctx)
            cw, _ = FX.measure_chip(name, fn, padding=(12, 4))
            FX.text_chip(canvas,
                         (cx - cw // 2, cy + avatar_size // 2 + 14),
                         name, fn,
                         fg=_pt,
                         bg=_pf,
                         bg_alpha=210, radius=10, padding=(12, 4))
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + rows_n * cell_h))
    return y + rows_n * cell_h


# ============================================================
# 10. cta_button — 行动按钮（大居中）
# ============================================================
def render_cta_button(canvas, y, ctx: RenderContext, data: dict) -> int:
    """v0.9.10：大居中报名按钮 + 可选上下提示文字。

    brief 字段：
      text:    按钮主文字（默认"立即报名"）
      pre_lines:  按钮上方 1~N 行小字（如"截止时间：2026 年 2 月 5 日 23:59"）
      post_lines: 按钮下方 1~N 行小字（如"名额：30 人"、"地点：IEG 28F"）
      hint:    与 pre/post 互斥的简写——单行字符串放在按钮下方
      tone:    "primary"（黄底黑字，默认）/ "outline"（米白底彩字描边）

    用户要求：直接把"报名方式"卡片去掉，改用大按钮 + 文字简介。
    """
    text = data.get("text") or data.get("button_text") or "立即报名"
    pre_lines = data.get("pre_lines") or []
    post_lines = data.get("post_lines") or []
    hint = data.get("hint") or data.get("button_hint")
    if hint and not post_lines:
        post_lines = [s for s in str(hint).split("\n") if s.strip()]

    panel_fill, text_color = _panel_pair(ctx)
    f_hint = ctx.font(28, role="body")
    body_kw = ctx.body_text_kwargs(fill=text_color)
    hint_line_h = 42
    hint_gap = 18  # 提示与按钮之间的间距

    f = ctx.font(56, role="display")
    bbox = f.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    btn_w = max(tw + 220, 520)
    btn_h = 140
    x0 = (ctx.width - btn_w) // 2
    accent_a = ctx.palette.get("accent_a", "#FBBF24")

    # 上方提示文字
    cy = y
    if pre_lines:
        d = ImageDraw.Draw(canvas)
        for line in pre_lines:
            lbb = f_hint.getbbox(line)
            lw = lbb[2] - lbb[0]
            d.text(((ctx.width - lw) // 2, cy), line, font=f_hint, **body_kw)
            cy += hint_line_h
        cy += hint_gap

    # 渐变按钮 + 内高光 + 强阴影
    btn_y = cy
    panel = FX.rounded_panel(
        (btn_w, btn_h), fill="#FFD66B", fill_b=accent_a,
        radius=70, border_color="#0E0F1A", border_width=5,
        add_highlight=True)
    FX.paste_with_shadow(canvas, panel, (x0, btn_y),
                         offset=(0, 16), blur=26, alpha=160)
    btn_text = _text_on(ctx, "accent_a", fallback_bg=accent_a)
    ImageDraw.Draw(canvas).text(
        (x0 + (btn_w - tw) // 2, btn_y + (btn_h - th) // 2 - 8),
        text, font=f, fill=btn_text)
    cy = btn_y + btn_h

    # 下方提示文字
    if post_lines:
        cy += hint_gap
        d = ImageDraw.Draw(canvas)
        for line in post_lines:
            lbb = f_hint.getbbox(line)
            lw = lbb[2] - lbb[0]
            d.text(((ctx.width - lw) // 2, cy), line, font=f_hint, **body_kw)
            cy += hint_line_h

    ctx.reserve((x0, y, x0 + btn_w, cy))
    return cy


# ============================================================
# 11. rules_box — 须知 / 纪律说明
# ============================================================
def render_rules_box(canvas, y, ctx: RenderContext, data: dict) -> int:
    heading = data.get("heading", "")
    bullets = data.get("bullets", [])
    fh = ctx.font(34)
    fb = ctx.font(28)
    line_h = 46
    pad = 30
    max_w = ctx.content_w - pad * 2
    body_lines = []
    for b in bullets:
        body_lines.extend(_wrap_text(f"· {b}", fb, max_w))
    panel_h = pad * 2 + (line_h + 8 if heading else 0) + line_h * len(body_lines)
    panel_fill, _ptext = _panel_pair(ctx)
    _frosted_panel(canvas, (ctx.content_x0, y, ctx.content_x1, y + panel_h),
                   radius=18, alpha=_panel_alpha(ctx, 215), fill_hex=panel_fill)
    cy = y + pad
    d = ImageDraw.Draw(canvas)
    accent_a = ctx.palette.get("accent_a", "#FBBF24")
    body_color = _ptext
    if heading:
        d.text((ctx.content_x0 + pad, cy), heading, font=fh, fill=accent_a)
        cy += line_h + 8
    for line in body_lines:
        d.text((ctx.content_x0 + pad, cy), line, font=fb, fill=body_color)
        cy += line_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ============================================================
# 12. contact_card — 联系人 + 二维码并排
# ============================================================
def render_contact_card(canvas, y, ctx: RenderContext, data: dict) -> int:
    text = data.get("text", "")
    contacts = data.get("contacts", [])
    f = ctx.font(30)
    line_h = 50
    pad = 30

    # 文案区（左 / 全宽）+ 二维码列（右）
    qr_size = 200
    qr_label_h = 40
    qr_col_total = qr_size + 24
    n_qr = len(contacts)
    qr_zone_w = n_qr * qr_col_total + (n_qr - 1) * 16 if n_qr > 0 else 0
    text_x1 = ctx.content_x1 - qr_zone_w - 24 if n_qr > 0 else ctx.content_x1
    max_text_w = (text_x1 - ctx.content_x0) - pad * 2
    lines = _wrap_text(text, f, max_text_w)
    text_h = pad * 2 + line_h * len(lines)
    qr_block_h = qr_size + qr_label_h + pad * 2
    panel_h = max(text_h, qr_block_h)

    panel_fill, _ptext = _panel_pair(ctx)
    _frosted_panel(canvas, (ctx.content_x0, y, ctx.content_x1, y + panel_h),
                   radius=18, alpha=_panel_alpha(ctx, 215), fill_hex=panel_fill)
    d = ImageDraw.Draw(canvas)
    body_color = _ptext
    cy = y + pad
    for line in lines:
        d.text((ctx.content_x0 + pad, cy), line, font=f, fill=body_color)
        cy += line_h

    # 二维码列
    qx = ctx.content_x1 - qr_zone_w
    fl = ctx.font(26)
    for c in contacts:
        # 白底
        bg = Image.new("RGBA", (qr_size + 16, qr_size + 16), (255, 255, 255, 255))
        canvas.alpha_composite(bg, (qx - 8, y + pad - 8))
        qr_path = c.get("qr")
        if qr_path:
            try:
                qr = Image.open(qr_path).convert("RGBA").resize((qr_size, qr_size), Image.LANCZOS)
                canvas.alpha_composite(qr, (qx, y + pad))
            except Exception:
                d.rectangle([qx, y + pad, qx + qr_size, y + pad + qr_size], fill="#222")
        else:
            cell = qr_size // 10
            for i in range(10):
                for j in range(10):
                    if (i + j) % 2 == 0:
                        d.rectangle(
                            [qx + i * cell, y + pad + j * cell,
                             qx + (i + 1) * cell, y + pad + (j + 1) * cell],
                            fill="#0E0F1A")
        # name —— v0.6: chip 替代描边
        name = c.get("name", "")
        if name:
            cw, _ = FX.measure_chip(name, fl, padding=(10, 4))
            FX.text_chip(canvas,
                         (qx + (qr_size - cw) // 2, y + pad + qr_size + 10),
                         name, fl,
                         fg="#FFFFFF",
                         bg=ctx.palette.get("primary", "#3B82F6"),
                         bg_alpha=230, radius=8, padding=(10, 4))
        qx += qr_col_total + 16
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ============================================================
# v0.9 模块化 · 新增 6 个渲染器
# 新增组件契约同前 13 个：render(canvas, y, ctx, data) -> y_next
# ============================================================

# ---------- 14. curriculum_timeline 课程时间轴 ----------
def render_curriculum_timeline(canvas, y, ctx: RenderContext, data: dict) -> int:
    """竖向时间轴：左侧圆点串联（dot 连线），右侧每个 part 一卡。
    字段：parts: [{label, time, format, topic, output}]，
         connector_style: dot | bar（默认 dot）
         with_faculty: 可选讲师小卡列表 [{name, title}]
    measure-first：先 wrap 每个 part 的字段，决定 part_h，再画 panel。"""
    parts = data.get("parts", []) or []
    if not parts:
        return y
    # v0.9.6：title 34→38 W7、meta 26→28、body 28→32 W7
    f_label = ctx.font(28, role="display")
    f_title = ctx.font(38, role="display")
    f_meta  = ctx.font(28)
    f_body  = ctx.font(32, role="display")
    pad_x, pad_y = 32, 26
    line_h_meta = 42
    line_h_body = 50
    gap_between = 28
    rail_x_off = 56                # 圆点列距左卡 28+18+10
    dot_r = 14
    card_w = ctx.content_w - rail_x_off
    card_x0 = ctx.content_x0 + rail_x_off

    panel_fill, _ptext = _panel_pair(ctx)
    accent_a   = ctx.palette.get("accent_a", "#FBBF24")
    accent_b   = ctx.palette.get("accent_b", "#A78BFA")

    # 第一遍：估每段卡片高度
    cards = []
    for p in parts:
        topic = p.get("topic", "")
        output = p.get("output", "")
        time_s = p.get("time", "")
        fmt    = p.get("format", "")
        # title = topic（必填），meta 行 = "时间 · 形式"
        meta_line = " · ".join([s for s in [time_s, fmt] if s])
        topic_lines = wrap_cjk(topic, f_title, card_w - pad_x * 2) if topic else []
        meta_lines  = wrap_cjk(meta_line, f_meta, card_w - pad_x * 2) if meta_line else []
        out_text    = f"产出：{output}" if output else ""
        out_lines   = wrap_cjk(out_text, f_body, card_w - pad_x * 2) if out_text else []
        h = pad_y * 2 + 36  # label 高度
        h += len(meta_lines) * line_h_meta + (10 if meta_lines else 0)
        h += len(topic_lines) * (line_h_body + 4)
        h += (8 + len(out_lines) * line_h_body) if out_lines else 0
        cards.append({"p": p, "h": h, "meta_lines": meta_lines,
                      "topic_lines": topic_lines, "out_lines": out_lines})

    total_h = sum(c["h"] for c in cards) + gap_between * (len(cards) - 1)

    # 画左侧 rail（贯穿所有 part）
    d = ImageDraw.Draw(canvas)
    rail_x = ctx.content_x0 + rail_x_off // 2
    d.line([(rail_x, y + 30), (rail_x, y + total_h - 30)], fill=accent_a, width=4)

    cy = y
    for idx, c in enumerate(cards):
        p = c["p"]
        ch = c["h"]
        # 圆点
        d.ellipse([rail_x - dot_r, cy + 30 - dot_r, rail_x + dot_r, cy + 30 + dot_r],
                  fill=accent_a, outline=panel_fill, width=4)
        # 卡片
        panel = FX.rounded_panel(
            (card_w, ch), fill=panel_fill,
            radius=18, alpha=_panel_alpha(ctx, 215), add_highlight=False,
            border_color=accent_a, border_width=2)
        FX.paste_with_shadow(canvas, panel, (card_x0, cy),
                             offset=(0, 8), blur=18, alpha=80)
        # label（Part 1 ...） 用 accent_b 小标签
        label = p.get("label", f"Part {idx + 1}")
        lbox = f_label.getbbox(label)
        lw = lbox[2] - lbox[0]
        chip_h = 36
        chip_panel = FX.rounded_panel(
            (lw + 24, chip_h), fill=accent_b, radius=10, add_highlight=False)
        canvas.alpha_composite(chip_panel, (card_x0 + pad_x, cy + pad_y - 4))
        d.text((card_x0 + pad_x + 12, cy + pad_y - 1), label, font=f_label,
               fill=_text_on(ctx, "accent_a", fallback_bg=accent_b))
        # meta line
        ty = cy + pad_y + chip_h + 10
        for line in c["meta_lines"]:
            d.text((card_x0 + pad_x, ty), line, font=f_meta, fill=accent_a)
            ty += line_h_meta
        # topic（主标题）
        for line in c["topic_lines"]:
            d.text((card_x0 + pad_x, ty), line, font=f_title, fill=_ptext)
            ty += line_h_body + 4
        # output
        if c["out_lines"]:
            ty += 4
            for line in c["out_lines"]:
                d.text((card_x0 + pad_x, ty), line, font=f_body, fill=_ptext)
                ty += line_h_body
        cy += ch + gap_between
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


# ---------- 15. faculty_grid 讲师团 ----------
def render_faculty_grid(canvas, y, ctx: RenderContext, data: dict) -> int:
    """讲师卡：layout=detail(≤2 大图大字) | compact(≤4 双列方/圆头像) | default(5+ 纵列单行)。
    字段：members [{avatar, name, title, bio}], avatar_shape=circle|square, layout"""
    members = data.get("members", []) or []
    if not members:
        return y
    layout = data.get("layout") or ("detail" if len(members) <= 2
                                     else ("compact" if len(members) <= 4 else "default"))
    shape = data.get("avatar_shape", "circle")
    accent_a = ctx.palette.get("accent_a", "#FBBF24")
    accent_b = ctx.palette.get("accent_b", "#A78BFA")
    panel_fill, _ptext = _panel_pair(ctx)

    if layout == "detail":
        return _render_faculty_detail(canvas, y, ctx, members, shape, accent_a, panel_fill, _ptext)
    elif layout == "compact":
        return _render_faculty_compact(canvas, y, ctx, members, shape, accent_a, panel_fill, _ptext)
    elif layout == "grid":
        cols = int(data.get("cols", 5))
        return _render_faculty_grid(canvas, y, ctx, members, shape, accent_a, panel_fill, _ptext, cols, data)
    else:
        return _render_faculty_default(canvas, y, ctx, members, shape, accent_a, panel_fill, _ptext)


def _draw_avatar(canvas, ctx, cx, cy, size, member, shape, accent,
                 ring_color=None, ring_width=None):
    """画一个头像：有 avatar 路径就贴图；否则用首字占位。
    ring_color / ring_width 可覆盖默认的描边样式（默认 accent 色 + 4px）。
    """
    d = ImageDraw.Draw(canvas)
    half = size // 2
    rc = ring_color or accent
    rw = int(ring_width) if ring_width is not None else 4
    avatar_path = member.get("avatar")
    if avatar_path:
        try:
            # 留出环宽空间，把头像缩到 size - 2*rw
            inner = max(8, size - 2 * rw)
            av = Image.open(avatar_path).convert("RGBA").resize(
                (inner, inner), Image.LANCZOS)
            mask = Image.new("L", av.size, 0)
            md = ImageDraw.Draw(mask)
            if shape == "circle":
                md.ellipse([0, 0, av.size[0], av.size[1]], fill=255)
            else:
                md.rounded_rectangle([0, 0, av.size[0], av.size[1]], radius=10, fill=255)
            canvas.paste(av, (cx - av.size[0] // 2, cy - av.size[1] // 2), mask)
            # 头像贴上后，再画外圈描边
            if shape == "circle":
                d.ellipse([cx - half, cy - half, cx + half, cy + half],
                          outline=rc, width=rw)
            else:
                d.rounded_rectangle([cx - half, cy - half, cx + half, cy + half],
                                    radius=14, outline=rc, width=rw)
            return
        except Exception:
            pass
    # 占位：先画底色 + 描边
    if shape == "circle":
        d.ellipse([cx - half, cy - half, cx + half, cy + half],
                  fill=ctx.palette.get("primary", "#3B82F6"),
                  outline=rc, width=rw)
    else:
        d.rounded_rectangle([cx - half, cy - half, cx + half, cy + half],
                            radius=14,
                            fill=ctx.palette.get("primary", "#3B82F6"),
                            outline=rc, width=rw)
    # 首字占位
    name = (member.get("name") or "T").strip()
    initial = name[0] if name else "T"
    f_init = ctx.font(int(size * 0.5), role="display")
    bbox = f_init.getbbox(initial)
    iw, ih = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - iw // 2 - bbox[0], cy - ih // 2 - bbox[1]),
           initial, font=f_init, fill="#FFFFFF")


def _render_faculty_detail(canvas, y, ctx, members, shape, accent, panel_fill, text_color):
    """≤2 人：每人一张大卡，左头像 + 右介绍。"""
    f_name  = ctx.font(40, role="display")
    f_title = ctx.font(28)
    f_bio   = ctx.font(28)
    avatar  = 200
    pad_x, pad_y = 36, 30
    line_h = 44
    gap = 28
    cy = y
    for m in members:
        max_text_w = ctx.content_w - pad_x * 2 - avatar - 32
        title_lines = wrap_cjk(m.get("title", ""), f_title, max_text_w)
        bio_lines = wrap_cjk(m.get("bio", ""), f_bio, max_text_w)
        h = pad_y * 2 + 50  # name
        h += len(title_lines) * 40 + (8 if title_lines else 0)
        h += (10 + len(bio_lines) * line_h) if bio_lines else 0
        h = max(h, avatar + pad_y * 2)
        panel = FX.rounded_panel(
            (ctx.content_w, h), fill=panel_fill, radius=18,
            alpha=_panel_alpha(ctx, 215), border_color=accent, border_width=2)
        FX.paste_with_shadow(canvas, panel, (ctx.content_x0, cy),
                             offset=(0, 8), blur=18, alpha=80)
        _draw_avatar(canvas, ctx, ctx.content_x0 + pad_x + avatar // 2,
                     cy + pad_y + avatar // 2, avatar, m, shape, accent)
        d = ImageDraw.Draw(canvas)
        tx = ctx.content_x0 + pad_x + avatar + 32
        ty = cy + pad_y
        d.text((tx, ty), m.get("name", ""), font=f_name, fill=accent)
        ty += 50
        for ln in title_lines:
            d.text((tx, ty), ln, font=f_title, fill=text_color)
            ty += 40
        if bio_lines:
            ty += 10
            for ln in bio_lines:
                d.text((tx, ty), ln, font=f_bio, fill=text_color)
                ty += line_h
        cy += h + gap
    total_h = cy - y - gap if members else 0
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


def _render_faculty_compact(canvas, y, ctx, members, shape, accent, panel_fill, text_color):
    """≤4 人：双列，每行一卡，左头像 + 右文字（紧凑版）。"""
    f_name  = ctx.font(32, role="display")
    f_title = ctx.font(24)
    f_bio   = ctx.font(24)
    avatar  = 120
    pad_x, pad_y = 24, 22
    line_h = 36
    gap = 20
    n = len(members)
    cols = 2
    cell_w = (ctx.content_w - gap) // cols

    # 第一遍量每个 cell 的高度
    cells = []
    for m in members:
        max_text_w = cell_w - pad_x * 2 - avatar - 18
        title_lines = wrap_cjk(m.get("title", ""), f_title, max_text_w)
        bio_lines = wrap_cjk(m.get("bio", ""), f_bio, max_text_w)
        h = pad_y * 2 + 42  # name
        h += len(title_lines) * 32 + (4 if title_lines else 0)
        h += (8 + len(bio_lines) * line_h) if bio_lines else 0
        h = max(h, avatar + pad_y * 2)
        cells.append({"m": m, "h": h, "title_lines": title_lines, "bio_lines": bio_lines})

    # 行高 = 当行最高
    row_heights = []
    for ri in range(0, n, cols):
        row_heights.append(max(c["h"] for c in cells[ri:ri + cols]))
    total_h = sum(row_heights) + gap * (len(row_heights) - 1)

    cy = y
    for ri, rh in enumerate(row_heights):
        for ci in range(cols):
            idx = ri * cols + ci
            if idx >= n:
                break
            c = cells[idx]
            x0 = ctx.content_x0 + ci * (cell_w + gap)
            panel = FX.rounded_panel(
                (cell_w, rh), fill=panel_fill, radius=18,
                alpha=_panel_alpha(ctx, 215), border_color=accent, border_width=2)
            FX.paste_with_shadow(canvas, panel, (x0, cy),
                                 offset=(0, 6), blur=14, alpha=70)
            _draw_avatar(canvas, ctx, x0 + pad_x + avatar // 2,
                         cy + pad_y + avatar // 2, avatar, c["m"], shape, accent)
            d = ImageDraw.Draw(canvas)
            tx = x0 + pad_x + avatar + 18
            ty = cy + pad_y
            d.text((tx, ty), c["m"].get("name", ""), font=f_name, fill=accent)
            ty += 42
            for ln in c["title_lines"]:
                d.text((tx, ty), ln, font=f_title, fill=text_color)
                ty += 32
            if c["bio_lines"]:
                ty += 4
                for ln in c["bio_lines"]:
                    d.text((tx, ty), ln, font=f_bio, fill=text_color)
                    ty += line_h
        cy += rh + gap
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


def _render_faculty_grid(canvas, y, ctx, members, shape, accent, panel_fill, text_color,
                         cols, data):
    """每行 N 人的头像网格：头像在上，姓名+职务在下；无卡片背景，避免视觉繁杂。
    字段（来自 data）：
      cols: 每行人数（默认 5）
      avatar_size: 头像直径/边长，默认按列宽自适应
      name_color / title_color：可覆盖
      gap_x / gap_y：水平 / 垂直间距
      pad_top / pad_bottom：整体上下留白
    """
    n = len(members)
    if n == 0:
        return y
    gap_x = int(data.get("gap_x", 28))
    gap_y = int(data.get("gap_y", 36))
    pad_top = int(data.get("pad_top", 8))
    pad_bottom = int(data.get("pad_bottom", 8))
    name_color = data.get("name_color", "#FFFFFF")
    title_color = data.get("title_color", text_color)
    ring_color = data.get("ring_color")  # 例：紫色 #9333EA；不填用 accent
    ring_width = data.get("ring_width", 6)

    cell_w = (ctx.content_w - gap_x * (cols - 1)) // cols
    avatar_size = int(data.get("avatar_size", min(cell_w - 24, 180)))
    f_name = ctx.font(int(data.get("name_font_size", 26)), role="display")
    f_title = ctx.font(int(data.get("title_font_size", 20)),
                       role=data.get("title_font_role", "body"))
    name_h = 32
    title_line_h = 28

    # 量每个 cell 的标题行数
    cells = []
    max_text_w = cell_w - 8
    max_title_lines = 0
    max_lines_cap = int(data.get("max_title_lines", 3))
    for m in members:
        title_lines = wrap_cjk(m.get("title", ""), f_title, max_text_w)
        # 限制最多 N 行
        if len(title_lines) > max_lines_cap:
            title_lines = title_lines[:max_lines_cap]
            last = title_lines[-1]
            while last and f_title.getbbox(last + "…")[2] > max_text_w:
                last = last[:-1]
            title_lines[-1] = (last + "…") if last else "…"
        cells.append({"m": m, "title_lines": title_lines})
        max_title_lines = max(max_title_lines, len(title_lines))

    row_h = avatar_size + 14 + name_h + 8 + max_title_lines * title_line_h
    rows = (n + cols - 1) // cols
    total_h = pad_top + rows * row_h + (rows - 1) * gap_y + pad_bottom

    # 可选：背景框（asset_frame / 纯色面板）
    panel_style = data.get("panel_style")
    asset_frame_path = data.get("asset_frame_path")
    if panel_style == "asset_frame" and asset_frame_path:
        # 包一层 asset_frame，需要内边距让头像/文字不顶到框边
        frame_inset = int(data.get("frame_inset", 28))
        try:
            _draw_asset_frame(canvas, ctx.content_x0, y,
                              ctx.content_w, total_h + frame_inset * 2,
                              asset_frame_path, corner=60)
            # 把整体内容下移 frame_inset，并相应增加 total_h
            y_offset = frame_inset
            total_h += frame_inset * 2
        except Exception as e:
            print(f"[warn] faculty_grid asset_frame 失败：{e}")
            y_offset = 0
    else:
        y_offset = 0

    d = ImageDraw.Draw(canvas)
    cy = y + pad_top + y_offset
    for ri in range(rows):
        # 该行的成员区间
        row_members = cells[ri * cols : (ri + 1) * cols]
        # 行内居中（最后一行不满时）
        row_count = len(row_members)
        row_total_w = row_count * cell_w + (row_count - 1) * gap_x
        x_start = ctx.content_x0 + (ctx.content_w - row_total_w) // 2
        for ci, c in enumerate(row_members):
            cell_x = x_start + ci * (cell_w + gap_x)
            # 头像中心
            avatar_cx = cell_x + cell_w // 2
            avatar_cy = cy + avatar_size // 2
            _draw_avatar(canvas, ctx, avatar_cx, avatar_cy, avatar_size,
                         c["m"], shape, accent,
                         ring_color=ring_color, ring_width=ring_width)
            # 姓名（居中，自适应字号：超出 cell_w-8 时按比例缩小）
            name = c["m"].get("name", "")
            f_n = f_name
            n_size = int(data.get("name_font_size", 26))
            avail_w = cell_w - 8
            nbox = f_n.getbbox(name)
            nw = nbox[2] - nbox[0]
            if nw > avail_w:
                # 按比例缩小姓名字号
                scale = avail_w / nw
                n_size = max(14, int(n_size * scale))
                f_n = ctx.font(n_size, role="display")
                nbox = f_n.getbbox(name)
                nw = nbox[2] - nbox[0]
            ty = cy + avatar_size + 14
            d.text((avatar_cx - nw // 2 - nbox[0], ty - nbox[1]),
                   name, font=f_n, fill=name_color)
            # 职务（多行居中）
            ty2 = ty + name_h + 8
            for ln in c["title_lines"]:
                tbox = f_title.getbbox(ln)
                tw = tbox[2] - tbox[0]
                d.text((avatar_cx - tw // 2 - tbox[0], ty2 - tbox[1]),
                       ln, font=f_title, fill=title_color)
                ty2 += title_line_h
        cy += row_h + gap_y

    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


def _render_faculty_default(canvas, y, ctx, members, shape, accent, panel_fill, text_color):
    """5+ 人：纵列单行小卡（简介可省略）。"""
    f_name  = ctx.font(30, role="display")
    f_title = ctx.font(24)
    avatar  = 86
    pad_x, pad_y = 22, 18
    gap = 14
    cy = y
    for m in members:
        max_text_w = ctx.content_w - pad_x * 2 - avatar - 18
        title_text = m.get("title", "")
        # 单行：name 一行，title 一行
        h = pad_y * 2 + 40 + (28 if title_text else 0)
        h = max(h, avatar + pad_y * 2)
        panel = FX.rounded_panel(
            (ctx.content_w, h), fill=panel_fill, radius=14,
            alpha=_panel_alpha(ctx, 200), border_color=accent, border_width=2)
        FX.paste_with_shadow(canvas, panel, (ctx.content_x0, cy),
                             offset=(0, 4), blur=10, alpha=60)
        _draw_avatar(canvas, ctx, ctx.content_x0 + pad_x + avatar // 2,
                     cy + pad_y + avatar // 2, avatar, m, shape, accent)
        d = ImageDraw.Draw(canvas)
        tx = ctx.content_x0 + pad_x + avatar + 18
        ty = cy + pad_y + 4
        d.text((tx, ty), m.get("name", ""), font=f_name, fill=accent)
        ty += 40
        if title_text:
            ty += 0
            d.text((tx, ty), title_text, font=f_title, fill=text_color)
        cy += h + gap
    total_h = cy - y - gap if members else 0
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


# ---------- 16. benefit_grid 收获 / 解决问题 四格 ----------
def render_benefit_grid(canvas, y, ctx: RenderContext, data: dict) -> int:
    """4 格图标 + 标题 + 一句话。字段：items [{icon, title, desc}], cols=2|4"""
    items = data.get("items", []) or []
    if not items:
        return y
    cols = data.get("cols", 2 if len(items) <= 4 else 4)
    gap = 20
    n = len(items)
    rows = (n + cols - 1) // cols
    cell_w = (ctx.content_w - gap * (cols - 1)) // cols
    f_title = ctx.font(30, role="display")
    f_desc  = ctx.font(24)
    pad_x, pad_y = 24, 24
    line_h = 36
    accent_a = data.get("accent_color") or ctx.palette.get("accent_a", "#FBBF24")
    if accent_a == "auto":
        accent_a = ctx.palette.get("accent_a", "#FBBF24")
    panel_fill, _ptext = _panel_pair(ctx)
    if data.get("text_color") and data.get("text_color") != "auto":
        _ptext = data.get("text_color")

    # 第一遍量每 cell 的高度
    cells = []
    for it in items:
        max_text_w = cell_w - pad_x * 2
        desc_lines = wrap_cjk(it.get("desc", ""), f_desc, max_text_w)
        h = pad_y * 2 + 60  # icon + title
        h += 40
        h += len(desc_lines) * line_h
        cells.append({"it": it, "h": h, "desc_lines": desc_lines})
    row_heights = []
    for ri in range(0, n, cols):
        row_heights.append(max(c["h"] for c in cells[ri:ri + cols]))
    total_h = sum(row_heights) + gap * (len(row_heights) - 1)

    cy = y
    for ri, rh in enumerate(row_heights):
        for ci in range(cols):
            idx = ri * cols + ci
            if idx >= n:
                break
            c = cells[idx]
            x0 = ctx.content_x0 + ci * (cell_w + gap)
            panel = FX.rounded_panel(
                (cell_w, rh), fill=panel_fill, radius=18,
                alpha=_panel_alpha(ctx, 215), border_color=accent_a, border_width=2)
            FX.paste_with_shadow(canvas, panel, (x0, cy),
                                 offset=(0, 6), blur=14, alpha=70)
            d = ImageDraw.Draw(canvas)
            # icon 区（占位：圆角彩色块 + 数字/字符）
            icon_size = 56
            ix = x0 + pad_x
            iy = cy + pad_y
            d.rounded_rectangle([ix, iy, ix + icon_size, iy + icon_size],
                                radius=14, fill=accent_a)
            icon_text = c["it"].get("icon") or str(idx + 1)
            f_icon = ctx.font(32, role="display")
            ibox = f_icon.getbbox(icon_text)
            iw, ih = ibox[2] - ibox[0], ibox[3] - ibox[1]
            d.text((ix + (icon_size - iw) // 2 - ibox[0],
                    iy + (icon_size - ih) // 2 - ibox[1]),
                   icon_text, font=f_icon,
                   fill=_text_on(ctx, "accent_a", fallback_bg=accent_a))
            # title
            ty = iy + icon_size + 10
            d.text((x0 + pad_x, ty), c["it"].get("title", ""),
                   font=f_title, fill=accent_a)
            ty += 40
            # desc
            for ln in c["desc_lines"]:
                d.text((x0 + pad_x, ty), ln, font=f_desc, fill=_ptext)
                ty += line_h
        cy += rh + gap
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


# ---------- 17. notice_box 注意事项（inline） ----------
def render_notice_box(canvas, y, ctx: RenderContext, data: dict) -> int:
    """与 rules_box 区别：默认无 heading（inline 嵌入正文），用 accent 边框 + ⚠ 装饰角。
    字段：bullets [str], inline=true（仅语义不同），accent_color=可覆盖"""
    bullets = data.get("bullets", []) or []
    if not bullets:
        return y
    accent = data.get("accent_color") or ctx.palette.get("accent_a", "#FBBF24")
    note_font_size = int(data.get("font_size", 32))
    fb = ctx.font(note_font_size, role=data.get("font_role", "display"))
    pad = 30
    line_h = max(38, note_font_size + 20)
    bullet_gap = 10
    max_w = ctx.content_w - pad * 2 - 36  # 让出 bullet 圆点宽
    panel_fill, _ptext = _panel_pair(ctx)
    if data.get("text_color") and data.get("text_color") != "auto":
        _ptext = data.get("text_color")

    # 支持 bullet 条目为 dict: {"text": str, "highlight": bool, "highlight_color": str}
    def _bullet_text(b):
        if isinstance(b, dict):
            return b.get("text", "")
        return str(b)
    def _bullet_color(b):
        if isinstance(b, dict) and b.get("highlight"):
            return b.get("highlight_color", "#FF3333")
        return None

    # 量
    items = []
    for b in bullets:
        lines = wrap_cjk(_bullet_text(b), fb, max_w)
        items.append((lines, _bullet_color(b)))
    body_h = sum(len(it[0]) * line_h for it in items) + bullet_gap * (len(items) - 1)
    panel_h = pad * 2 + body_h
    panel = FX.rounded_panel(
        (ctx.content_w, panel_h), fill=panel_fill, radius=18,
        alpha=_panel_alpha(ctx, 200), border_color=accent, border_width=3)
    FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                         offset=(0, 6), blur=14, alpha=70)
    d = ImageDraw.Draw(canvas)
    # v0.9.7：左上角"注意"标签字号 22→30、tag 80x32→120x46，
    # 与正文 32W7 视觉权重匹配（用户反馈太小）。
    f_tag = ctx.font(30, role="display")
    tag_text = "注意"
    tbb = f_tag.getbbox(tag_text)
    tw = tbb[2] - tbb[0]
    th = tbb[3] - tbb[1]
    tag_w = max(120, tw + 36)
    tag_h = 46
    tag = FX.rounded_panel((tag_w, tag_h), fill=accent, radius=10, add_highlight=False)
    canvas.alpha_composite(tag, (ctx.content_x0 + 24, y - tag_h // 2))
    d.text((ctx.content_x0 + 24 + (tag_w - tw) // 2 - tbb[0],
            y - tag_h // 2 + (tag_h - th) // 2 - tbb[1]),
           tag_text, font=f_tag,
           fill=_text_on(ctx, "accent_a", fallback_bg=accent))
    # bullets
    cy = y + pad
    for lines, hl_color in items:
        text_fill = hl_color if hl_color else _ptext
        # 圆点（highlight 时也用红色）
        dot_fill = hl_color if hl_color else accent
        d.ellipse([ctx.content_x0 + pad, cy + 16,
                   ctx.content_x0 + pad + 10, cy + 26], fill=dot_fill)
        for li, ln in enumerate(lines):
            d.text((ctx.content_x0 + pad + 24, cy), ln, font=fb, fill=text_fill)
            cy += line_h
        cy += bullet_gap
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ---------- 18. contact_inline 联系方式（v0.10.1：支持文字 / 二维码两形态） ----------
def render_contact_inline(canvas, y, ctx: RenderContext, data: dict) -> int:
    """底部联系方式。

    字段：
      text (str)     必填，主联系文案（如"联系人：dorrainzeng（曾子河）"）
      mode "text"|"qr"  默认 text；qr 模式时右侧贴二维码 PNG
      qr_image (str) 二维码图片路径（mode=qr 必填）
      qr_label (str) 二维码下方说明（默认"扫码联系"）
      qr_size (int)  二维码边长（默认 160）

    用户要求：① 字体改为 W7 加粗（之前 W3 太弱）；② 兼容扫码场景。
    """
    text = data.get("text", "") or ""
    if not text:
        return y
    mode = (data.get("mode") or "text").lower()

    contact_font_size = int(data.get("font_size", 28))
    f = ctx.font(contact_font_size, role=data.get("font_role", "display"))
    pad = 22
    line_h = max(36, contact_font_size + 16)
    panel_fill, _ptext = _panel_pair(ctx)
    if data.get("text_color") and data.get("text_color") != "auto":
        _ptext = data.get("text_color")

    if mode == "qr" and data.get("qr_image"):
        qr_size = int(data.get("qr_size", 160))
        qr_label = data.get("qr_label") or "扫码联系"
        # 文案左、二维码右；panel 高度取两者较大
        text_w = ctx.content_w - 48 - qr_size - 32  # 留出二维码宽 + 间距
        lines = wrap_cjk(text, f, text_w)
        text_h = len(lines) * line_h
        f_qr_label = ctx.font(22, role="body")
        label_h = 30
        qr_total_h = qr_size + 8 + label_h
        panel_h = pad * 2 + max(text_h, qr_total_h)

        panel = FX.rounded_panel(
            (ctx.content_w, panel_h), fill=panel_fill, radius=14,
            alpha=_panel_alpha(ctx, 180), add_highlight=False)
        FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                             offset=(0, 4), blur=10, alpha=60)
        d = ImageDraw.Draw(canvas)
        # 文字（左侧，垂直居中）
        cy = y + (panel_h - text_h) // 2
        for ln in lines:
            d.text((ctx.content_x0 + 24, cy), ln, font=f, fill=_ptext)
            cy += line_h
        # 二维码（右侧，垂直居中）
        try:
            qr_img = Image.open(data["qr_image"]).convert("RGBA")
            qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
            qx = ctx.content_x1 - 24 - qr_size
            qy = y + (panel_h - qr_total_h) // 2
            canvas.alpha_composite(qr_img, (qx, qy))
            # 二维码下方 label
            f_lbl = f_qr_label
            lbb = f_lbl.getbbox(qr_label)
            lw = lbb[2] - lbb[0]
            d.text((qx + (qr_size - lw) // 2, qy + qr_size + 6),
                   qr_label, font=f_lbl, **ctx.body_text_kwargs(fill=_ptext))
        except Exception as e:
            print(f"[warn] contact qr 加载失败: {e}")
        ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
        return y + panel_h

    # mode=text（默认）：纯文字单/多行居中。支持显式 \n 换行：每段再 wrap。
    max_w = ctx.content_w - 48
    lines = []
    for seg in text.split("\n"):
        if seg.strip() == "":
            lines.append("")
            continue
        lines.extend(wrap_cjk(seg, f, max_w))
    panel_h = pad * 2 + len(lines) * line_h
    panel = FX.rounded_panel(
        (ctx.content_w, panel_h), fill=panel_fill, radius=14,
        alpha=_panel_alpha(ctx, 180), add_highlight=False)
    FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                         offset=(0, 4), blur=10, alpha=60)
    d = ImageDraw.Draw(canvas)
    cy = y + pad
    for ln in lines:
        bbox = f.getbbox(ln)
        tw = bbox[2] - bbox[0]
        d.text((ctx.content_x0 + (ctx.content_w - tw) // 2, cy),
               ln, font=f, fill=_ptext)
        cy += line_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ---------- 19. bullet_points_block 大块项目符号 ----------
def render_bullet_points_block(canvas, y, ctx: RenderContext, data: dict) -> int:
    """『你将获得 / 解决的问题』整体一卡，编号每条另起一行。
    字段：bullets [str], number_style=circle|square|none（默认 circle）"""
    bullets = data.get("bullets", []) or []
    if not bullets:
        return y
    style = data.get("number_style", "circle")
    bullet_font_size = int(data.get("font_size", 36))
    fb = ctx.font(bullet_font_size, role=data.get("font_role", "display"))
    f_num = ctx.font(max(20, bullet_font_size - 8), role="display")
    pad_x, pad_y = 36, 30
    line_h = max(40, bullet_font_size + 22)
    gap = 18
    num_w = 44 if style != "none" else 0
    max_w = ctx.content_w - pad_x * 2 - num_w - 16
    accent_a = data.get("accent_color") or ctx.palette.get("accent_a", "#FBBF24")
    if accent_a == "auto":
        accent_a = ctx.palette.get("accent_a", "#FBBF24")
    panel_fill, _ptext = _panel_pair(ctx)
    if data.get("text_color") and data.get("text_color") != "auto":
        _ptext = data.get("text_color")
    # 量
    rows = []
    for i, b in enumerate(bullets):
        lines = wrap_cjk(b, fb, max_w)
        rows.append(lines)
    body_h = sum(len(r) * line_h for r in rows) + gap * (len(rows) - 1)
    panel_h = pad_y * 2 + body_h
    panel = FX.rounded_panel(
        (ctx.content_w, panel_h), fill=panel_fill, radius=20,
        alpha=_panel_alpha(ctx, 215), border_color=accent_a, border_width=2)
    FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                         offset=(0, 8), blur=18, alpha=80)
    d = ImageDraw.Draw(canvas)
    cy = y + pad_y
    for i, lines in enumerate(rows):
        # 编号
        if style != "none":
            nx = ctx.content_x0 + pad_x
            ny = cy + 4
            if style == "circle":
                d.ellipse([nx, ny, nx + 36, ny + 36], fill=accent_a)
            else:
                d.rounded_rectangle([nx, ny, nx + 36, ny + 36], radius=8, fill=accent_a)
            num_text = str(i + 1)
            nbox = f_num.getbbox(num_text)
            nw = nbox[2] - nbox[0]
            nh = nbox[3] - nbox[1]
            d.text((nx + (36 - nw) // 2 - nbox[0], ny + (36 - nh) // 2 - nbox[1]),
                   num_text, font=f_num,
                   fill=_text_on(ctx, "accent_a", fallback_bg=accent_a))
        for li, ln in enumerate(lines):
            d.text((ctx.content_x0 + pad_x + num_w + 16, cy),
                   ln, font=fb, fill=_ptext)
            cy += line_h
        cy += gap
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ============================================================
# 13. footer_logobar — 底部合作单位 logo 一字排
# ============================================================
def render_footer_logobar(canvas, y, ctx: RenderContext, data: dict) -> int:
    logos = data.get("logos", [])
    bar_h = 160
    # 半透明黑底带 + 顶边高光线
    bar = FX.rounded_panel(
        (ctx.width - 80, bar_h), fill="#0A0A24", fill_b="#1B1840",
        radius=18, alpha=200, add_highlight=True)
    FX.paste_with_shadow(canvas, bar, (40, y),
                         offset=(0, 8), blur=18, alpha=110)

    # 没传 logos 时，自动放 IEG 横版白 logo + wordmark 双联
    if not logos:
        ieg_h = 64
        ieg = ctx.logo("horizontal", target_height=ieg_h)
        wm = ctx.logo("wordmark", target_height=int(ieg_h * 0.7))
        if ieg is not None and wm is not None:
            total_w = ieg.width + 40 + wm.width
            x_start = (ctx.width - total_w) // 2
            canvas.alpha_composite(ieg, (x_start, y + (bar_h - ieg.height) // 2))
            canvas.alpha_composite(wm, (x_start + ieg.width + 40, y + (bar_h - wm.height) // 2))
        elif ieg is not None:
            canvas.alpha_composite(ieg, ((ctx.width - ieg.width) // 2,
                                         y + (bar_h - ieg.height) // 2))
        else:
            f = ctx.font(28)
            text = "腾讯互动娱乐事业群（IEG）"
            bbox = f.getbbox(text)
            tw = bbox[2] - bbox[0]
            ImageDraw.Draw(canvas).text(
                ((ctx.width - tw) // 2, y + (bar_h - bbox[3]) // 2),
                text, font=f, fill=_text_on(ctx, "dark", fallback_bg="#0A0A24"))
        ctx.reserve((40, y, ctx.width - 40, y + bar_h))
        return y + bar_h

    n = len(logos)
    cell_w = (ctx.width - 80) // n
    h = int(bar_h * 0.55)
    fb_color = _text_on(ctx, "dark", fallback_bg="#0A0A24")
    for i, lp in enumerate(logos):
        cx = 40 + i * cell_w + cell_w // 2
        try:
            lg = Image.open(lp).convert("RGBA")
            ratio = h / lg.height
            lg = lg.resize((int(lg.width * ratio), h), Image.LANCZOS)
            canvas.alpha_composite(lg, (cx - lg.width // 2, y + (bar_h - h) // 2))
        except Exception:
            d = ImageDraw.Draw(canvas)
            d.rectangle([cx - 60, y + 40, cx + 60, y + bar_h - 40],
                        outline=fb_color, width=2)
            d.text((cx - 24, y + bar_h // 2 - 12), f"L{i+1}",
                   font=ctx.font(26), fill=fb_color)
    ctx.reserve((40, y, ctx.width - 40, y + bar_h))
    return y + bar_h


# ============================================================
# 14. top_logo_bar — v0.9.4 透明顶/底 logo 条（不占模块槽，无任何元素重叠）
# ============================================================
def render_top_logo_bar(canvas, y, ctx: RenderContext, data: dict) -> int:
    """轻量 logo 条：透明背景，仅承载 1~N 个 logo 横向并排。

    与 footer_logobar 的差别：
    - 没有黑底面板、没有阴影、不画背景。完全依赖海报底色。
    - 只画 logo（按 brightness 自动选 color/black/white 变体），与所有其他元素零重叠。
    - 自身高度 = max(logo_h) + pad*2，调用方拿到的 y_next 已经是 logo 之下的留白起点。

    字段：
      logos: [str path]   （必填，按顺序左→右等距分布）
      logo_height: int    单个 logo 目标高度，默认 76
      align: "center"|"left"|"right"  整体对齐，默认 center
      gap: int            logo 之间的水平间距，默认 80
      pad_top / pad_bottom: int  上下留白，默认 24/24
      bg: 故意不支持 —— 铁律：透明 / 不画背景。
    """
    logo_paths = list(dict.fromkeys(data.get("logos") or []))
    if not logo_paths:
        return y
    logo_h = int(data.get("logo_height", 76))
    # logo_heights: 数组，为每个 logo 单独指定高度（不足时回退 logo_height）
    logo_heights = data.get("logo_heights") or []
    gap = int(data.get("gap", 80))
    pad_top = int(data.get("pad_top", 24))
    pad_bottom = int(data.get("pad_bottom", 24))
    align = data.get("align", "center")

    loaded = []
    max_logo_w = int(data.get("logo_max_width") or min(300, max(160, ctx.content_w * 0.22)))
    for i, lp in enumerate(logo_paths):
        try:
            im = Image.open(lp).convert("RGBA")
            h = int(logo_heights[i]) if i < len(logo_heights) else logo_h
            ratio = min(h / max(1, im.height), max_logo_w / max(1, im.width))
            im = im.resize((max(1, int(im.width * ratio)), max(1, int(im.height * ratio))), Image.LANCZOS)
            loaded.append(im)
        except Exception as e:
            print(f"[warn] top_logo_bar 加载失败 {lp}: {e}")
    if not loaded:
        return y

    gap = min(gap, max(24, int(ctx.content_w * 0.06)))
    total_w = sum(im.width for im in loaded) + gap * (len(loaded) - 1)
    if total_w > ctx.content_w and total_w > 0:
        scale = min(1.0, ctx.content_w / total_w)
        loaded = [
            im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
            for im in loaded
        ]
        gap = int(gap * scale)
        total_w = sum(im.width for im in loaded) + gap * (len(loaded) - 1)
    max_h = max(im.height for im in loaded)
    bar_h = max_h + pad_top + pad_bottom

    # ---- v0.9.5 铁律：logo 直接坐在底色渐变上，不再画单色挡条。----

    cy_base = y + pad_top
    if len(loaded) > 1 and data.get("distribution") == "even_grid":
        cell_w = ctx.content_w / len(loaded)
        for i, im in enumerate(loaded):
            center_x = ctx.content_x0 + cell_w * (i + 0.5)
            cy = cy_base + (max_h - im.height) // 2
            canvas.alpha_composite(im, (int(center_x - im.width / 2), cy))
    else:
        if align == "left":
            x_start = ctx.content_x0
        elif align == "right":
            x_start = ctx.content_x1 - total_w
        else:
            x_start = (ctx.width - total_w) // 2
        cx = x_start
        for im in loaded:
            cy = cy_base + (max_h - im.height) // 2
            canvas.alpha_composite(im, (cx, cy))
            cx += im.width + gap
    # 整条注册禁飞区（带左右安全 margin），装饰避让
    ctx.reserve((0, max(y - 8, 0), ctx.width, y + bar_h), pad=4)
    return y + bar_h


# ============================================================
# 21. data_table — 通用二维表格（v0.10）
# ============================================================
def render_data_table(canvas, y, ctx: RenderContext, data: dict) -> int:
    """通用表格组件：给二维数据，引擎管列宽 / wrap / 表头 / 斑马纹。

    brief 字段：
      headers: ["时间","内容","形式","产出"]   表头（必填）
      rows:    [["1.20 14:00","管理跃迁开篇","线下","自评"], ...]
      align:   ["left","left","center","center"] 各列对齐（可选，默认 left）
      col_weights: [1.4, 2.0, 1.0, 1.4] 各列宽度权重（可选，默认 1）
      style:   "soft" | "zebra" | "minimal"  默认 soft
      accent_color: 表头底色（可选，默认 palette.accent_a）

    设计原则：light 配色 panel 走米白 + 表头深字 + accent 描边；
              dark 配色走深底 + 白字。所有文字 measure-first 自动 wrap。
    """
    headers = data.get("headers") or []
    rows = data.get("rows") or []
    if not headers or not rows:
        return y

    n_cols = len(headers)
    aligns = (data.get("align") or ["left"] * n_cols)[:n_cols]
    while len(aligns) < n_cols:
        aligns.append("left")
    weights = data.get("col_weights")  # 用户可显式给；否则自动测量
    style = data.get("style", "soft")
    accent = data.get("accent_color") or ctx.palette.get("accent_a", "#FBBF24")

    # 尺寸
    pad = 24
    cell_pad_x = 18
    cell_pad_y = 16
    table_w = ctx.content_w
    inner_w = table_w - pad * 2

    head_font_size = int(data.get("header_font_size", 28))
    cell_font_size = int(data.get("font_size", 28))
    f_head = ctx.font(head_font_size, role="display")  # 表头 W7
    f_cell = ctx.font(cell_font_size, role=data.get("font_role", "body"))
    intro_text = str(data.get("intro") or data.get("text") or data.get("content") or "").strip()
    intro_font_size = int(data.get("intro_font_size") or max(24, cell_font_size))
    f_intro = ctx.font(intro_font_size, role=data.get("intro_font_role", "body"))
    line_h = max(40, max(head_font_size, cell_font_size) + 12)
    intro_line_h = max(34, int(intro_font_size * 1.4))

    # v0.10.1：智能列宽 —— 量出每列真实最长内容（表头与数据），
    # 再按"natural width + 自适应剩余空间"分配。
    # 用户反馈"表格换行不对"根因：之前手写 col_weights 只是经验值，
    # 不会考虑实际数据宽度；遇到"业务复盘工作坊"这种长词会断词。
    def _measure_natural(col_idx: int) -> int:
        """该列最长内容（非换行情况下）需要的像素宽（含 cell_pad_x*2）。"""
        max_w = f_head.getbbox(str(headers[col_idx]))[2]
        for row in rows:
            if col_idx < len(row):
                bbox = f_cell.getbbox(str(row[col_idx] or ""))
                max_w = max(max_w, bbox[2])
        return max_w + cell_pad_x * 2

    if weights is None:
        natural_widths = [_measure_natural(i) for i in range(n_cols)]
        total_natural = sum(natural_widths)
        if total_natural <= inner_w:
            # 全部能放下：先按 natural 分，再把剩余空间均摊给所有列
            extra = inner_w - total_natural
            col_widths = [w + extra // n_cols for w in natural_widths]
            col_widths[-1] = inner_w - sum(col_widths[:-1])
        else:
            # 装不下：按 natural 比例缩放（让短列保留 natural，长列让出来 wrap）
            # 找出短列（natural <= inner_w/n_cols 的列锁定 natural），
            # 剩余空间分给长列。
            avg = inner_w / n_cols
            short_idx = [i for i, w in enumerate(natural_widths) if w <= avg]
            long_idx = [i for i in range(n_cols) if i not in short_idx]
            short_total = sum(natural_widths[i] for i in short_idx)
            long_pool = inner_w - short_total
            long_natural_total = sum(natural_widths[i] for i in long_idx) or 1
            col_widths = [0] * n_cols
            for i in short_idx:
                col_widths[i] = natural_widths[i]
            for i in long_idx:
                col_widths[i] = int(long_pool * natural_widths[i] / long_natural_total)
            col_widths[-1] = inner_w - sum(col_widths[:-1])
    else:
        # 用户显式给了 col_weights：尊重它
        weights_list = list(weights)[:n_cols]
        while len(weights_list) < n_cols:
            weights_list.append(1.0)
        total_w = sum(weights_list) or 1
        col_widths = [int(inner_w * (w / total_w)) for w in weights_list]
        col_widths[-1] = inner_w - sum(col_widths[:-1])

    # measure：每行 wrap 后行数
    def cell_lines(text, w):
        if text is None:
            return [""]
        return wrap_cjk(str(text), f_cell, max(40, w - cell_pad_x * 2))

    head_lines_per_col = [wrap_cjk(str(h), f_head, max(40, col_widths[i] - cell_pad_x * 2))
                          for i, h in enumerate(headers)]
    head_max_lines = max(len(c) for c in head_lines_per_col)
    head_h = head_max_lines * line_h + cell_pad_y * 2

    rows_lines = []
    rows_h = []
    for row in rows:
        cells = []
        max_lines = 1
        for ci in range(n_cols):
            text = row[ci] if ci < len(row) else ""
            ls = cell_lines(text, col_widths[ci])
            cells.append(ls)
            max_lines = max(max_lines, len(ls))
        rows_lines.append(cells)
        rows_h.append(max_lines * line_h + cell_pad_y * 2)

    intro_lines = _wrap_text_block(intro_text, f_intro, inner_w) if intro_text else []
    intro_h = len(intro_lines) * intro_line_h
    intro_gap = 12 if intro_lines else 0
    table_h = head_h + sum(rows_h)
    panel_h = pad * 2 + intro_h + intro_gap + table_h

    # 1) 外层 panel（light 米白 / dark 深底）
    panel_fill, text_color = _panel_pair(ctx)
    if data.get("text_color") and data.get("text_color") != "auto":
        text_color = data.get("text_color")
    panel = FX.rounded_panel(
        (table_w, panel_h), fill=panel_fill, radius=18,
        alpha=_panel_alpha(ctx, 215),
        border_color=accent, border_width=2)
    FX.paste_with_shadow(canvas, panel, (ctx.content_x0, y),
                         offset=(0, 8), blur=20,
                         alpha=60 if _brightness(ctx) == "light" else 80)

    # 2) 表头条
    d = ImageDraw.Draw(canvas)
    table_x0 = ctx.content_x0 + pad
    table_y0 = y + pad
    if intro_lines:
        intro_color = data.get("intro_color") or text_color
        iy = table_y0
        for line in intro_lines:
            d.text((table_x0, iy), line, font=f_intro, fill=intro_color)
            iy += intro_line_h
        table_y0 = iy + intro_gap
    head_y = table_y0
    # 表头底色：accent，圆角顶部
    head_panel = FX.rounded_panel(
        (inner_w, head_h), fill=accent, radius=12, add_highlight=False)
    canvas.alpha_composite(head_panel, (table_x0, head_y))
    head_text_color = data.get("header_color") or _text_on(ctx, "accent_a", fallback_bg=accent) or "#0E0F1A"

    # 表头文字
    cx = table_x0
    for ci, lines in enumerate(head_lines_per_col):
        cw = col_widths[ci]
        # 垂直居中
        text_h = len(lines) * line_h
        ty = head_y + (head_h - text_h) // 2
        for ln in lines:
            tw_ = f_head.getbbox(ln)[2] - f_head.getbbox(ln)[0]
            if aligns[ci] == "center":
                tx = cx + (cw - tw_) // 2
            elif aligns[ci] == "right":
                tx = cx + cw - tw_ - cell_pad_x
            else:
                tx = cx + cell_pad_x
            d.text((tx, ty), ln, font=f_head, fill=head_text_color)
            ty += line_h
        cx += cw

    # 3) 数据行
    cy = head_y + head_h
    body_kw = ctx.body_text_kwargs(fill=text_color)
    for ri, cells in enumerate(rows_lines):
        rh = rows_h[ri]
        # 斑马纹
        if style == "zebra" and ri % 2 == 1:
            zebra = FX.rounded_panel(
                (inner_w, rh), fill=accent, radius=0,
                alpha=_panel_alpha(ctx, 35), add_highlight=False)
            canvas.alpha_composite(zebra, (table_x0, cy))
        # 行底分隔线（minimal 风）
        if style in ("soft", "minimal"):
            d.line([(table_x0 + 6, cy + rh - 1),
                    (table_x0 + inner_w - 6, cy + rh - 1)],
                   fill=(*hex_to_rgb(accent), 60) if style == "soft" else accent,
                   width=1)
        # 单元格文字
        cx = table_x0
        for ci, lines in enumerate(cells):
            cw = col_widths[ci]
            text_h = len(lines) * line_h
            ty = cy + (rh - text_h) // 2
            for ln in lines:
                tw_ = f_cell.getbbox(ln)[2] - f_cell.getbbox(ln)[0]
                if aligns[ci] == "center":
                    tx = cx + (cw - tw_) // 2
                elif aligns[ci] == "right":
                    tx = cx + cw - tw_ - cell_pad_x
                else:
                    tx = cx + cell_pad_x
                d.text((tx, ty), ln, font=f_cell, **body_kw)
                ty += line_h
            cx += cw
        cy += rh

    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


# ============================================================
# 23. asset_frame — 用素材PNG作为panel背景（九宫格拉伸）
# ============================================================
def _draw_asset_frame(canvas: Image.Image, x0: int, y0: int, w: int, h: int,
                      asset_path: str, corner: int = 60):
    """将 asset_path 图片用九宫格拉伸到 (w, h)，贴到 canvas 的 (x0, y0)。
    corner: 四角不拉伸区域大小（像素），默认60。
    """
    src = Image.open(asset_path).convert("RGBA")
    sw, sh = src.size
    c = min(corner, sw // 3, sh // 3)

    def crop(x0s, y0s, x1s, y1s):
        return src.crop((x0s, y0s, x1s, y1s))

    patches = [
        crop(0,    0,    c,    c),
        crop(c,    0,    sw-c, c),
        crop(sw-c, 0,    sw,   c),
        crop(0,    c,    c,    sh-c),
        crop(c,    c,    sw-c, sh-c),
        crop(sw-c, c,    sw,   sh-c),
        crop(0,    sh-c, c,    sh),
        crop(c,    sh-c, sw-c, sh),
        crop(sw-c, sh-c, sw,   sh),
    ]
    mw = max(w - 2 * c, 1)
    mh = max(h - 2 * c, 1)

    def rz(p, tw, th):
        return p.resize((max(tw, 1), max(th, 1)), Image.LANCZOS)

    result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for img, px, py in [
        (rz(patches[0], c,  c),   0,    0),
        (rz(patches[1], mw, c),   c,    0),
        (rz(patches[2], c,  c),   c+mw, 0),
        (rz(patches[3], c,  mh),  0,    c),
        (rz(patches[4], mw, mh),  c,    c),
        (rz(patches[5], c,  mh),  c+mw, c),
        (rz(patches[6], c,  c),   0,    c+mh),
        (rz(patches[7], mw, c),   c,    c+mh),
        (rz(patches[8], c,  c),   c+mw, c+mh),
    ]:
        result.alpha_composite(img, (px, py))

    canvas.alpha_composite(result, (x0, y0))


# ============================================================
# 24. render_complex_table — 支持 colspan/rowspan 的复杂表格
# ============================================================
def render_complex_table(canvas, y, ctx: RenderContext, data: dict) -> int:
    """支持合并单元格的复杂表格。专业排版规范：

    设计原则（固化到 SKILL.md）：
      1. 列宽分配：col_weights 指定权重，引擎根据内容最小宽度下限保证可读性
      2. 英文换行：使用 wrap_cjk，保证英文单词不在单词中间断行
      3. 合并单元格框线：仅在真实单元格边界画竖线，被 rowspan/colspan 覆盖的
         区域内部不画任何分隔线，避免视觉混乱
      4. 行高：以该行所有单元格（含多行文本）计算最大值，保证文字不溢出
      5. 垂直居中：文字在单元格内垂直居中

    brief 字段：
      headers: [{"text":"模块","colspan":1,"align":"center"}, ...]
      rows: 行数组，每行为 cell 数组
        cell: {"text":"...", "colspan":1, "rowspan":1, "bold":false, "align":"left"}
      col_count: 总列数
      col_weights: 各列宽度权重（影响最终分配，但下限受内容约束）
      accent_color: 表头底色（默认 #9333EA）
      asset_frame: 素材框路径（可选）
      pad: 外边距（默认 20）
      font_size: 正文字号（默认 26，推荐 22-28 范围）
    """
    PAD = data.get("pad", 20)
    col_count = data.get("col_count", 3)
    col_weights = list(data.get("col_weights") or [1.0] * col_count)
    accent_hex = data.get("accent_color") or ctx.palette.get("accent_a", "#9333EA")
    asset_frame_path = data.get("asset_frame")
    font_size = int(data.get("font_size", 26))

    total_w = ctx.content_w - PAD * 2
    f_head = ctx.font(font_size + 2, role="display")
    f_cell = ctx.font(font_size, role="body")
    CELL_PAD_X = max(8, int(14 * font_size / 26))
    CELL_PAD_Y = max(8, int(12 * font_size / 26))
    LINE_H = max(26, int(40 * font_size / 26))
    MIN_COL_W = font_size * 3   # 最窄列不低于3个字宽

    # ── 第一步：按 col_weights 分配基础列宽，但保证每列不低于 MIN_COL_W ──
    weight_sum = sum(col_weights) or col_count
    col_widths = [max(MIN_COL_W, int(total_w * w / weight_sum)) for w in col_weights]
    # 补足误差到最后一列（避免右边出现空隙）
    diff = total_w - sum(col_widths)
    col_widths[-1] += diff

    def _wrap(text, w, bold=False):
        """单元格内换行，英文单词保持完整。"""
        f = f_head if bold else f_cell
        avail = max(w - CELL_PAD_X * 2, MIN_COL_W)
        return _wrap_text(text, f, avail)

    def _cell_h(text, w, bold=False):
        lines = _wrap(text, w, bold)
        return len(lines) * LINE_H + CELL_PAD_Y * 2

    def _draw_text(d, cx, cy, cw, ch, text, bold=False, align="left", fill="#FFFFFF"):
        f = f_head if bold else f_cell
        lines = _wrap(text, cw, bold)
        total_th = len(lines) * LINE_H
        ty = cy + max(0, (ch - total_th) // 2)
        for ln in lines:
            if not ln:
                ty += LINE_H
                continue
            bbox = f.getbbox(ln)
            tw = bbox[2] - bbox[0]
            if align == "center":
                tx = cx + (cw - tw) // 2
            elif align == "right":
                tx = cx + cw - tw - CELL_PAD_X
            else:
                tx = cx + CELL_PAD_X
            d.text((tx, ty - bbox[1]), ln, font=f, fill=fill)
            ty += LINE_H

    # ── 解析表头 ──
    headers = data.get("headers", [])
    head_row_h = max(LINE_H + CELL_PAD_Y * 2, 52)
    hi_tmp = 0
    for hcell in headers:
        htxt = hcell.get("text", "") if isinstance(hcell, dict) else str(hcell)
        hcs = hcell.get("colspan", 1) if isinstance(hcell, dict) else 1
        hcw = sum(col_widths[hi_tmp:hi_tmp + hcs])
        head_row_h = max(head_row_h, _cell_h(htxt, hcw, bold=True))
        hi_tmp += hcs

    # ── 解析数据行（建立 occupied 网格，跟踪 rowspan/colspan） ──
    rows = data.get("rows", [])
    max_rows = len(rows)
    occupied = [[False] * col_count for _ in range(max_rows)]
    parsed_rows = []

    for ri, row in enumerate(rows):
        ci_canvas = 0
        parsed_cells = []
        for cell in row:
            while ci_canvas < col_count and occupied[ri][ci_canvas]:
                ci_canvas += 1
            if ci_canvas >= col_count:
                break
            if isinstance(cell, str):
                cell = {"text": cell}
            cs = min(cell.get("colspan", 1), col_count - ci_canvas)
            rs = cell.get("rowspan", 1)
            # 标记占用（dr/dc > 0 的才标记，自身不标）
            for dr in range(rs):
                for dc in range(cs):
                    if (dr > 0 or dc > 0) and ri + dr < max_rows and ci_canvas + dc < col_count:
                        occupied[ri + dr][ci_canvas + dc] = True
            cw_total = sum(col_widths[ci_canvas:ci_canvas + cs])
            parsed_cells.append({
                "text": cell.get("text", ""),
                "colspan": cs, "rowspan": rs,
                "bold": cell.get("bold", False),
                "align": cell.get("align", "left"),
                "col_idx": ci_canvas,
                "cell_w": cw_total,
            })
            ci_canvas += cs
        parsed_rows.append(parsed_cells)

    # ── 计算行高（考虑跨行合并：跨行单元格的内容高度分摊到各行） ──
    # 初始每行高度 = 该行非跨行单元格的最大高度
    row_heights = [max(LINE_H + CELL_PAD_Y * 2, 44)] * max_rows
    for ri, pcells in enumerate(parsed_rows):
        for cell in pcells:
            rs = cell["rowspan"]
            if rs == 1:
                h = _cell_h(cell["text"], cell["cell_w"], cell["bold"])
                row_heights[ri] = max(row_heights[ri], h)

    # 跨行单元格：确保 sum(row_heights[ri:ri+rs]) >= 单元格内容高度
    for ri, pcells in enumerate(parsed_rows):
        for cell in pcells:
            rs = cell["rowspan"]
            if rs > 1:
                needed = _cell_h(cell["text"], cell["cell_w"], cell["bold"])
                current = sum(row_heights[ri:ri + rs])
                if needed > current:
                    extra = needed - current
                    row_heights[ri + rs - 1] += extra  # 把多余高度加到最后一行

    total_h = head_row_h + sum(row_heights) + PAD * 2
    start_x = ctx.content_x0 + PAD
    start_y = y + PAD

    # ── 背景框 ──
    if asset_frame_path:
        try:
            _draw_asset_frame(canvas, ctx.content_x0, y,
                              ctx.content_w, total_h, asset_frame_path, corner=70)
        except Exception:
            _frosted_panel(canvas, (ctx.content_x0, y, ctx.content_x1, y + total_h),
                           radius=20, alpha=185, fill_hex="#160830")
    else:
        _frosted_panel(canvas, (ctx.content_x0, y, ctx.content_x1, y + total_h),
                       radius=20, alpha=185, fill_hex="#160830")

    d = ImageDraw.Draw(canvas)
    BORDER = "#9B59D4"           # 表格线颜色（低对比度紫，不抢眼）
    BORDER_THICK = "#CC66FF"     # 强调线（表头分隔）

    # ── 绘制表头 ──
    hx = start_x
    hi = 0
    for hcell in headers:
        if isinstance(hcell, dict):
            htxt = hcell.get("text", "")
            hcs = hcell.get("colspan", 1)
            halign = hcell.get("align", "center")
        else:
            htxt = str(hcell)
            hcs = 1
            halign = "center"
        hcw = sum(col_widths[hi:hi + hcs])
        # 表头背景
        hr_img = Image.new("RGBA", (hcw, head_row_h), (0, 0, 0, 0))
        hr_d = ImageDraw.Draw(hr_img)
        r, g, b = hex_to_rgb(accent_hex)
        hr_d.rectangle([0, 0, hcw, head_row_h], fill=(r, g, b, 210))
        canvas.alpha_composite(hr_img, (hx, start_y))
        _draw_text(d, hx, start_y, hcw, head_row_h, htxt, bold=True,
                   align=halign, fill="#FFFFFF")
        # 列竖线（仅真实列边界）
        if hi > 0:
            d.line([(hx, start_y), (hx, start_y + head_row_h)],
                   fill=BORDER_THICK, width=1)
        hx += hcw
        hi += hcs

    head_bottom_y = start_y + head_row_h
    d.line([(start_x, head_bottom_y), (start_x + total_w, head_bottom_y)],
           fill=BORDER_THICK, width=2)

    # ── 构建行 y 坐标映射 ──
    cum = head_bottom_y
    row_y_map = [cum]
    for rh in row_heights:
        cum += rh
        row_y_map.append(cum)

    # ── 构建"真实边界"集合，用于决定是否画竖线 ──
    # real_borders[ri] = set of x positions（start_x 偏移量）that are true column boundaries
    # 跨列单元格的内部列位置不是真实边界
    def _build_real_borders():
        """对每行，计算哪些列 x 位置有真实竖线边界。"""
        borders_per_row = []
        for ri in range(max_rows):
            bounds = set()
            bounds.add(0)  # 最左边总是边界
            bounds.add(total_w)  # 最右边总是边界
            for cell in parsed_rows[ri]:
                ci = cell["col_idx"]
                cs = cell["colspan"]
                # 单元格左边界
                left_x = sum(col_widths[:ci])
                bounds.add(left_x)
                # 单元格右边界
                right_x = sum(col_widths[:ci + cs])
                bounds.add(right_x)
            borders_per_row.append(sorted(bounds))
        return borders_per_row

    real_borders = _build_real_borders()

    # ── 绘制数据行 ──
    for ri, parsed_cells in enumerate(parsed_rows):
        cy = row_y_map[ri]
        rh = row_heights[ri]

        # 斑马纹（交替行轻微高亮）
        if ri % 2 == 1:
            zeb = Image.new("RGBA", (total_w, rh), (0, 0, 0, 0))
            ImageDraw.Draw(zeb).rectangle([0, 0, total_w - 1, rh - 1],
                                          fill=(120, 60, 200, 25))
            canvas.alpha_composite(zeb, (start_x, cy))

        # 绘制单元格文字
        for cell in parsed_cells:
            ci = cell["col_idx"]
            cs = cell["colspan"]
            rs = cell["rowspan"]
            cw = cell["cell_w"]
            # 跨行高度
            ch = sum(row_heights[ri:ri + rs])
            cx = start_x + sum(col_widths[:ci])
            _draw_text(d, cx, cy, cw, ch, cell["text"],
                       bold=cell["bold"], align=cell["align"], fill="#FFFFFF")

        # 竖分隔线：只在该行的真实边界处画（排除最左和最右，它们由外框负责）
        for bx in real_borders[ri]:
            if bx == 0 or bx == total_w:
                continue
            # 计算跨越哪些行（相同边界连续向下直到行边界变化）
            line_end_y = row_y_map[ri + 1]
            # 向下延伸：如果下一行也有这个边界，延伸到下一行底部
            for rj in range(ri + 1, max_rows):
                if bx in set(real_borders[rj]):
                    line_end_y = row_y_map[rj + 1]
                else:
                    break
            # 只画当前行高度内的线（避免重复）
            d.line([(start_x + bx, cy), (start_x + bx, row_y_map[ri + 1])],
                   fill=BORDER, width=1)

        # 行底横线（分段绘制：跨过此行底的 rowspan 单元格区域跳过）
        # 收集被 rowspan 覆盖（跨越此行底）的列范围
        if ri < max_rows - 1:
            skip_ranges = []  # [(x_start_rel, x_end_rel)] 相对于 start_x
            for rk in range(ri + 1):
                for cell in parsed_rows[rk]:
                    rs_k = cell["rowspan"]
                    ci_k = cell["col_idx"]
                    cs_k = cell["colspan"]
                    # 该单元格从 rk 行开始，跨 rs_k 行，若其结束行 > ri，则覆盖行底 ri
                    if rk + rs_k - 1 > ri:
                        x0_rel = sum(col_widths[:ci_k])
                        x1_rel = sum(col_widths[:ci_k + cs_k])
                        skip_ranges.append((x0_rel, x1_rel))

            if not skip_ranges:
                # 无跳过，画完整横线
                d.line([(start_x, row_y_map[ri + 1]),
                        (start_x + total_w, row_y_map[ri + 1])],
                       fill=BORDER, width=1)
            else:
                # 合并跳过区间
                skip_ranges.sort()
                merged = []
                for s, e in skip_ranges:
                    if merged and s <= merged[-1][1]:
                        merged[-1] = (merged[-1][0], max(merged[-1][1], e))
                    else:
                        merged.append([s, e])
                # 分段画横线
                cur_x = 0
                line_y = row_y_map[ri + 1]
                for sx, ex in merged:
                    if cur_x < sx:
                        d.line([(start_x + cur_x, line_y),
                                (start_x + sx, line_y)], fill=BORDER, width=1)
                    cur_x = ex
                if cur_x < total_w:
                    d.line([(start_x + cur_x, line_y),
                            (start_x + total_w, line_y)], fill=BORDER, width=1)

    # 外框圆角矩形
    d.rounded_rectangle(
        [ctx.content_x0, y, ctx.content_x1, y + total_h],
        radius=16, outline=BORDER_THICK, width=2)

    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


# ============================================================
# 22. subtitle_text — 艺术字下方的副标题文字（如"正式开营啦！"）
# ============================================================
def render_subtitle_text(canvas, y, ctx: RenderContext, data: dict) -> int:
    """在 hero_strip 艺术字下方渲染一行带游戏风格效果的副标题。

    效果：白色字体 + 紫色外描边 + 外发光 + 可选装饰框。
    字段：
      text: str           副标题内容
      font_size: int      字号，默认 56
      pad_top / pad_bottom: int  上下留白，默认 8/8
      frame_style: str    装饰框风格，"diamond"（菱形角双线框，默认）或 "none"
    """
    text = data.get("text", "")
    if not text:
        return y

    font_size = int(data.get("font_size", 56))
    pad_top = int(data.get("pad_top", 8))
    pad_bottom = int(data.get("pad_bottom", 8))
    # 🔒 铁律 v0.10.3：副标题装饰框默认关闭（"none"），不得改为 "diamond" 等样式
    frame_style = data.get("frame_style", "none")

    f = ctx.font(font_size, role="display")
    bbox = f.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # offset_x: 视觉居中微调（如带 ! 等右侧偏旁字符时，视觉重心偏左，需要整体右移）
    offset_x = int(data.get("offset_x", 0))
    tx = (ctx.width - tw) // 2 + offset_x
    ty = y + pad_top

    stroke_w = max(3, font_size // 14)

    # -- 步骤1：在独立图层上画文字，再模糊生成发光光晕 --
    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.text((tx, ty), text, font=f, fill=(200, 100, 255, 220),
            stroke_width=stroke_w + 6, stroke_fill=(180, 80, 255, 180))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=font_size // 6))
    canvas.alpha_composite(glow_layer)

    # -- 步骤2：装饰框（在文字后面画，不遮字） --
    if frame_style != "none":
        draw_frame = ImageDraw.Draw(canvas)
        frame_pad_x = int(font_size * 1.2)
        frame_pad_y = int(font_size * 0.45)
        fx0 = tx - frame_pad_x
        fy0 = ty - frame_pad_y
        fx1 = tx + tw + frame_pad_x
        fy1 = ty + th + frame_pad_y + stroke_w

        line_col  = (200, 120, 255, 200)   # 亮紫
        line_col2 = (160,  80, 220, 120)   # 暗紫（第二条线）
        lw = max(2, font_size // 20)
        gap = max(4, font_size // 12)      # 双线间距

        # 外框
        draw_frame.rectangle([fx0, fy0, fx1, fy1], outline=line_col, width=lw)
        # 内框（双线效果）
        draw_frame.rectangle(
            [fx0 + gap, fy0 + gap, fx1 - gap, fy1 - gap],
            outline=line_col2, width=max(1, lw - 1)
        )

        # 菱形角装饰（四角各画一个小菱形）
        d = int(font_size * 0.32)
        corners = [(fx0, fy0), (fx1, fy0), (fx0, fy1), (fx1, fy1)]
        for cx_, cy_ in corners:
            diamond = [
                (cx_, cy_ - d),
                (cx_ + d, cy_),
                (cx_, cy_ + d),
                (cx_ - d, cy_),
            ]
            draw_frame.polygon(diamond, fill=(180, 80, 255, 200))
            draw_frame.polygon(diamond, outline=(220, 140, 255, 255), width=max(1, lw - 1))

        # 左右两侧各画一条水平短横线（延伸装饰）
        ext = int(font_size * 0.6)
        mid_y = (fy0 + fy1) // 2
        draw_frame.line([(fx0 - ext, mid_y), (fx0 - 2, mid_y)], fill=line_col, width=lw)
        draw_frame.line([(fx1 + 2, mid_y), (fx1 + ext, mid_y)], fill=line_col, width=lw)

    # -- 步骤3：紫色描边文字层 --
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (tx, ty), text, font=f,
        fill=(255, 255, 255, 255),
        stroke_width=stroke_w,
        stroke_fill=(150, 50, 220, 255),
    )

    bar_h = th + stroke_w * 2 + pad_top + pad_bottom + int(font_size * 0.45) * 2
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + bar_h))
    return y + bar_h


# ---------------------------------------------------------------------------
# render_table_module_section
# ---------------------------------------------------------------------------
# 插件入口：将 poster_table_module 渲染的复杂表格图像 paste 进海报画布。
#
# Brief data 字段（与 poster_table_module 的 brief 格式完全一致）：
#   sections      : list  必填，表格数据
#   title         : str   可选，表格标题
#   theme         : str   可选，配色主题（purple_tech / blue_business / orange_vivid）
#   notice        : dict  可选，通知栏 {icon, text}
#   pad_top       : int   可选，上边距（默认 24）
#   pad_bottom    : int   可选，下边距（默认 24）
#   scale         : int   可选，DPI 倍率（默认 2，高清）
# ---------------------------------------------------------------------------

def render_table_module_section(canvas, y, ctx: RenderContext, data: dict) -> int:
    """调用 poster_table_module 渲染复杂表格，并合成到海报画布。"""
    import sys, os
    _lib_dir = os.path.dirname(os.path.abspath(__file__))
    if _lib_dir not in sys.path:
        sys.path.insert(0, _lib_dir)
    from poster_table_module import render_table_module  # type: ignore

    pad_top    = int(data.get("pad_top", 24))
    pad_bottom = int(data.get("pad_bottom", 24))
    scale      = int(data.get("scale", 2))

    # 传给 poster_table_module 的 brief（剥掉布局字段）
    module_brief = {k: v for k, v in data.items()
                    if k not in ("type", "pad_top", "pad_bottom", "scale")}

    # 渲染得到 RGBA PIL.Image
    module_img = render_table_module(
        module_brief,
        scale=scale,
        canvas_width=ctx.width,
    )

    # 按海报实际宽度缩放（poster_table_module 输出宽度=canvas_width*scale）
    if module_img.width != ctx.width:
        new_h = int(module_img.height * ctx.width / module_img.width)
        module_img = module_img.resize((ctx.width, new_h), Image.LANCZOS)

    paste_y = y + pad_top

    # canvas 可能是 RGB，需要用 RGBA 临时层 alpha_composite 后 paste 回
    if canvas.mode == "RGBA":
        canvas.alpha_composite(module_img, (0, paste_y))
    else:
        tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        tmp.alpha_composite(module_img, (0, paste_y))
        canvas.paste(tmp.convert("RGB"), (0, 0), tmp.split()[3])

    total_h = module_img.height + pad_top + pad_bottom
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


def render_image_block(canvas, y, ctx: RenderContext, data: dict) -> int:
    """直接把一张图片按内容宽等比缩放后贴到当前 y 位置。

    brief 字段：
      image_path : str   图片路径（必填）
      pad_top    : int   顶部留白，默认 16
      pad_bottom : int   底部留白，默认 16
      width_ratio: float 相对于 content_w 的宽度比例，默认 1.0（撑满内容区）
      align      : str   "left" | "center" | "right"，默认 "center"
    """
    image_path = data.get("image_path", "")
    pad_top    = int(data.get("pad_top", 16))
    pad_bottom = int(data.get("pad_bottom", 16))
    width_ratio = float(data.get("width_ratio", 1.0))
    align = data.get("align", "center")

    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"[warn] image_block 加载失败: {e}")
        return y + pad_top + pad_bottom

    target_w = int(ctx.content_w * width_ratio)
    ratio = target_w / img.width
    target_h = int(img.height * ratio)
    img = img.resize((target_w, target_h), Image.LANCZOS)

    if align == "left":
        x = ctx.content_x0
    elif align == "right":
        x = ctx.content_x1 - target_w
    else:
        x = ctx.content_x0 + (ctx.content_w - target_w) // 2

    paste_y = y + pad_top
    if canvas.mode == "RGBA":
        canvas.alpha_composite(img, (x, paste_y))
    else:
        tmp = canvas.convert("RGBA")
        tmp.alpha_composite(img, (x, paste_y))
        canvas.paste(tmp.convert("RGB"), (0, 0))

    total_h = pad_top + target_h + pad_bottom
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + total_h))
    return y + total_h


# ============================================================
# v0.11 Spec renderers — 规格化版式能力
# ============================================================
def _spec_panel(canvas, ctx, x0, y0, x1, y1, radius=28, fill=None, outline=None):
    if isinstance(fill, str) and fill == "transparent":
        return
    fill = fill or ctx.palette.get("panel_dark", "#243D73")
    outline = outline or ctx.palette.get("accent_b", "#B86CFF")
    layer = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r, g, b = hex_to_rgb(fill)
    ar, ag, ab = hex_to_rgb(outline)
    d.rounded_rectangle([0, 0, x1 - x0, y1 - y0], radius=radius, fill=(r, g, b, 218))
    d.rounded_rectangle([1, 1, x1 - x0 - 2, y1 - y0 - 2], radius=radius, outline=(ar, ag, ab, 150), width=3)
    FX.paste_with_shadow(canvas, layer, (x0, y0), offset=(0, 10), blur=24, alpha=90)


def _spec_draw_panel(canvas, ctx, data, x0, y0, x1, y1, radius=28, fill=None, outline=None):
    mode = data.get("module_frame_mode")
    panel_style = data.get("panel_style")
    if mode == "none" or panel_style == "none":
        return
    frame = data.get("asset_frame_path") or data.get("asset_frame") or data.get("module_frame_path")
    if frame and (mode in (None, "upload") or panel_style == "asset_frame"):
        try:
            _draw_asset_frame(canvas, x0, y0, x1 - x0, y1 - y0, frame, corner=70)
            return
        except Exception as e:
            print(f"[warn] spec asset frame failed: {e}")
    _spec_panel(canvas, ctx, x0, y0, x1, y1, radius=radius, fill=fill or data.get("fill"), outline=outline or data.get("outline"))


def _spec_section_title(canvas, ctx, x, y, title, font_size=42, accent=None) -> int:
    if not title:
        return y
    accent = accent or ctx.palette.get("accent_a", "#D276FF")
    f = ctx.font(font_size, role="display")
    fill = "#FFFFFF"
    d = ImageDraw.Draw(canvas)
    d.text((x, y), title, font=f, fill=fill, stroke_width=2, stroke_fill="#1B1740")
    bb = f.getbbox(title)
    d.rounded_rectangle([x, y + bb[3] + 10, x + min(230, max(110, bb[2] - bb[0] + 36)), y + bb[3] + 18], radius=4, fill=accent)
    return y + max(70, bb[3] - bb[1] + 28)


def _spec_title_value(data: dict, default: str) -> str:
    if data.get("hide_title"):
        return ""
    if "title" in data:
        return data.get("title") or ""
    return default


def _spec_text_color(data: dict, ctx: RenderContext, fallback="#EEF4FF") -> str:
    color = data.get("text_color")
    if color and color != "auto":
        return color
    fill = data.get("fill")
    if isinstance(fill, str) and fill not in {"", "auto", "transparent"}:
        try:
            return pick_text_color_on(hex_to_rgb(fill))
        except Exception:
            pass
    return fallback if _brightness(ctx) != "light" else "#1F2937"


def _spec_load_image(path, size, mode="cover", radius=24, fallback_label="IMAGE"):
    w, h = size
    try:
        img = Image.open(_resolve_path(path)).convert("RGBA")
        if mode == "contain":
            img.thumbnail((w, h), Image.LANCZOS)
            out = Image.new("RGBA", (w, h), (255, 255, 255, 0))
            out.alpha_composite(img, ((w - img.width) // 2, (h - img.height) // 2))
        else:
            out = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
    except Exception:
        out = Image.new("RGBA", (w, h), (38, 61, 115, 255))
        fd = ImageDraw.Draw(out)
        fd.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=(50, 79, 145, 255), outline=(160, 190, 255, 120), width=3)
        fd.text((max(12, w // 2 - 42), max(12, h // 2 - 14)), fallback_label[:12], fill=(230, 238, 255, 210))
    if radius:
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
        out.putalpha(Image.composite(out.getchannel("A"), mask, mask))
    return out


def _spec_draw_action(canvas, ctx, box, action: dict):
    text = action.get("text") or "立即报名"
    x0, y0, x1, y1 = box
    accent = action.get("color") or ctx.palette.get("accent_a", "#F8C94A")
    r, g, b = hex_to_rgb(accent)
    btn = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    d = ImageDraw.Draw(btn)
    d.rounded_rectangle([0, 0, x1 - x0, y1 - y0], radius=(y1 - y0) // 2, fill=(r, g, b, 240))
    d.rounded_rectangle([2, 2, x1 - x0 - 2, y1 - y0 - 2], radius=(y1 - y0) // 2, outline=(255, 255, 255, 120), width=2)
    f = ctx.font(30, role="display")
    bb = f.getbbox(text)
    d.text(((x1 - x0 - (bb[2] - bb[0])) // 2, (y1 - y0 - (bb[3] - bb[1])) // 2 - 4), text, font=f, fill=pick_text_color_on(hex_to_rgb(accent)))
    FX.paste_with_shadow(canvas, btn, (x0, y0), offset=(0, 8), blur=14, alpha=100)


def _spec_rich_text_segments(raw: str):
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw or "")
    raw = re.sub(r"(?i)</(div|p|li|h\d)>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html_lib.unescape(raw).replace("\xa0", " ")
    parts = []
    for chunk in raw.split("\n"):
        line = re.sub(r"[ \t]+", " ", chunk).strip()
        if line:
            parts.append(line)
    return "\n".join(parts).strip()


def _path_from_skill_asset_url(value: str) -> str:
    raw = html_lib.unescape(str(value or ""))
    if not raw:
        return ""
    if "/api/skill-asset" in raw and "path=" in raw:
        try:
            from urllib.parse import parse_qs, urlparse, unquote
            parsed = urlparse(raw)
            qs = parse_qs(parsed.query or "")
            return unquote((qs.get("path") or [raw])[0])
        except Exception:
            m = re.search(r'[?&]path=([^&]+)', raw)
            return html_lib.unescape(m.group(1)) if m else raw
    m = re.search(r'/api/asset/([^/]+)/([^?#]+)', raw)
    if m:
        try:
            from urllib.parse import unquote
            session = unquote(m.group(1))
            filename = unquote(m.group(2))
            # _COMPONENTS_ROOT = gaming-training-poster, sibling poster-web holds uploads.
            candidate = _COMPONENTS_ROOT.parent / "poster-web" / "uploads" / session / filename
            if candidate.exists():
                return str(candidate)
        except Exception:
            pass
    return raw


def _spec_rich_image_meta(tag: str, image_lookup: dict) -> dict:
    path = ""
    width_pct = 0.0
    align = "center"
    m = re.search(r'data-asset-path=["\']([^"\']+)["\']', tag or "")
    if m:
        path = html_lib.unescape(m.group(1))
    srcm = re.search(r'\bsrc=["\']([^"\']+)["\']', tag or "")
    if not path and srcm:
        path = _path_from_skill_asset_url(srcm.group(1))
    wm_data = re.search(r'data-width-pct=["\']([^"\']+)["\']', tag or "")
    if wm_data:
        try:
            width_pct = max(0.08, min(1.0, float(wm_data.group(1))))
        except Exception:
            pass
    am = re.search(r'data-align=["\']([^"\']+)["\']', tag or "")
    if am and am.group(1) in {"left", "center", "right"}:
        align = am.group(1)
    style = re.search(r'style=["\']([^"\']+)["\']', tag or "")
    if style:
        sm = style.group(1)
        wm_pct = re.search(r'width\s*:\s*([0-9.]+)%', sm)
        wm_px = re.search(r'width\s*:\s*([0-9.]+)px', sm)
        if wm_pct:
            width_pct = max(0.08, min(1.0, float(wm_pct.group(1)) / 100.0))
        elif wm_px:
            width_pct = max(0.08, min(1.0, float(wm_px.group(1)) / 720.0))
    linked = image_lookup.get(path) if path else None
    if isinstance(linked, dict):
        width_pct = float(linked.get("width_pct") or linked.get("widthPct") or width_pct or 0)
    return {"path": path, "width_pct": width_pct or 0.55, "align": align}


def _spec_blocks_from_rich_html(raw_html: str, font, content_w: int, images: list) -> list:
    if not raw_html:
        return []
    image_lookup = {}
    for item in images or []:
        if isinstance(item, dict) and item.get("path"):
            image_lookup[str(item.get("path"))] = item
    blocks = []
    pattern = re.compile(r'<(?:span|div)\b(?=[^>]*(?:class=["\'][^"\']*rich-image-resizer|data-type=["\']poster-image))[\s\S]*?</(?:span|div)>', re.I)
    pos = 0
    for m in pattern.finditer(raw_html):
        text = _spec_rich_text_segments(raw_html[pos:m.start()])
        if text:
            blocks.append(("body", _wrap_text_block(text, font, content_w)))
        meta = _spec_rich_image_meta(m.group(0), image_lookup)
        if meta.get("path"):
            blocks.append(("image", [meta]))
        pos = m.end()
    tail = _spec_rich_text_segments(raw_html[pos:])
    if tail:
        blocks.append(("body", _wrap_text_block(tail, font, content_w)))
    return blocks


def _spec_rich_image_box(item, content_w: int):
    meta = item if isinstance(item, dict) else {"path": str(item or "")}
    pct = float(meta.get("width_pct") or meta.get("widthPct") or 1.0)
    display_w = int(max(160, min(content_w, content_w * pct)))
    path = _path_from_skill_asset_url(meta.get("path") or meta.get("src") or "")
    ratio = 0.62
    try:
        img = Image.open(_resolve_path(path))
        if img.width > 0:
            ratio = img.height / img.width
    except Exception:
        pass
    display_h = int(max(110, min(520, display_w * ratio)))
    return path, display_w, display_h



# ============================================================
# TipTap / ProseMirror editor_json 渲染
# ============================================================
def _editor_json_image_meta(node: dict) -> dict:
    attrs = node.get("attrs") or {}
    path = attrs.get("path") or attrs.get("data-asset-path") or ""
    src = attrs.get("src") or ""
    pct = attrs.get("widthPct", attrs.get("width_pct", 0.55))
    try:
        pct = max(0.08, min(0.48, float(pct)))
    except Exception:
        pct = 0.55
    align = attrs.get("align") or attrs.get("textAlign") or "center"
    if align not in {"left", "center", "right"}:
        align = "center"
    return {"path": _path_from_skill_asset_url(path or src), "src": src, "width_pct": pct, "align": align}


def _editor_mark_style(marks: list, base: dict) -> dict:
    style = dict(base or {})
    for mark in marks or []:
        if not isinstance(mark, dict):
            continue
        mt = mark.get("type")
        attrs = mark.get("attrs") or {}
        if mt == "bold":
            style["bold"] = True
        elif mt == "italic":
            style["italic"] = True
        elif mt == "underline":
            style["underline"] = True
        elif mt == "textStyle":
            if attrs.get("color"):
                style["color"] = attrs.get("color")
            if attrs.get("fontSize"):
                try:
                    style["font_size"] = int(float(str(attrs.get("fontSize")).replace("px", "")))
                except Exception:
                    pass
            if attrs.get("fontFamily"):
                style["font_family"] = attrs.get("fontFamily")
        elif mt == "highlight":
            if attrs.get("color"):
                style["background"] = attrs.get("color")
    return style


def _editor_json_inline_runs(node: dict, base_style: dict) -> list:
    runs = []
    def walk(n, inherited):
        if not isinstance(n, dict):
            return
        nt = n.get("type")
        if nt == "text":
            text = n.get("text") or ""
            if text:
                runs.append({"text": text, "style": _editor_mark_style(n.get("marks") or [], inherited)})
            return
        if nt == "hardBreak":
            runs.append({"text": "\n", "style": dict(inherited)})
            return
        next_style = _editor_mark_style(n.get("marks") or [], inherited)
        for child in n.get("content") or []:
            walk(child, next_style)
    for child in node.get("content") or []:
        walk(child, base_style)
    return runs

def _editor_json_paragraph_blocks(node: dict, base_style: dict, data: dict) -> list:
    blocks = []
    text_node = {"type": node.get("type") or "paragraph", "attrs": node.get("attrs") or {}, "content": []}
    image_row = []

    def flush_text():
        nonlocal text_node
        runs = _editor_json_inline_runs(text_node, base_style)
        if runs:
            attrs = node.get("attrs") or {}
            blocks.append({"type": "rich_text", "runs": runs, "align": attrs.get("textAlign") or data.get("text_align") or "left"})
        text_node = {"type": node.get("type") or "paragraph", "attrs": node.get("attrs") or {}, "content": []}

    def flush_images():
        nonlocal image_row
        if image_row:
            blocks.append({"type": "image_row", "items": image_row, "align": (node.get("attrs") or {}).get("textAlign") or data.get("text_align") or "center"})
        image_row = []

    for child in node.get("content") or []:
        if isinstance(child, dict) and child.get("type") in {"posterImage", "image"}:
            flush_text()
            image_row.append(_editor_json_image_meta(child))
        elif isinstance(child, dict) and child.get("type") == "text" and not (child.get("text") or "").replace("\u200b", "").strip() and image_row:
            # FIX: 问题3 - 编辑器为行内图片插入的零宽/普通空格不应打断图片并排行。
            continue
        else:
            flush_images()
            text_node.setdefault("content", []).append(child)
    flush_text()
    flush_images()
    return blocks


def _editor_json_blocks(editor_json: dict, data: dict, ctx: RenderContext) -> list:
    if not isinstance(editor_json, dict) or editor_json.get("type") != "doc":
        return []
    base_style = {
        "font_size": int(data.get("font_size") or 31),
        "color": _spec_text_color(data, ctx),
        "bold": data.get("font_weight") == "bold",
        "italic": data.get("font_style") == "italic",
        "underline": data.get("text_decoration") == "underline",
    }
    blocks = []
    def walk_block(node):
        if not isinstance(node, dict):
            return
        nt = node.get("type")
        if nt in {"posterImage", "image"}:
            blocks.append({"type": "image", "meta": _editor_json_image_meta(node)})
        elif nt in {"paragraph", "heading", "listItem"}:
            blocks.extend(_editor_json_paragraph_blocks(node, base_style, data))
        elif nt in {"bulletList", "orderedList"}:
            for child in node.get("content") or []:
                walk_block(child)
        else:
            for child in node.get("content") or []:
                walk_block(child)
    for child in editor_json.get("content") or []:
        walk_block(child)
    return blocks


def _rich_run_font(ctx: RenderContext, run: dict, data: dict):
    style = run.get("style") or {}
    fs = int(style.get("font_size") or data.get("font_size") or 31)
    role = "display" if style.get("bold") else "body"
    return ctx.font(max(8, min(160, fs)), role=role)


def _run_text_width(font, text: str) -> int:
    if not text:
        return 0
    bb = font.getbbox(text)
    return max(0, bb[2] - bb[0])


def _split_rich_text_units(text: str) -> list[str]:
    parts = []
    buf = ""
    for ch in text:
        if ch == "\n":
            if buf:
                parts.append(buf); buf = ""
            parts.append("\n")
        elif ch.isspace():
            buf += ch
            parts.append(buf); buf = ""
        elif ord(ch) < 128 and (ch.isalnum() or ch in "_-./@"):
            buf += ch
        else:
            if buf:
                parts.append(buf); buf = ""
            parts.append(ch)
    if buf:
        parts.append(buf)
    return parts


def _wrap_rich_runs(runs: list, ctx: RenderContext, data: dict, max_width: int) -> list:
    lines = []
    current = []
    current_w = 0
    for run in runs:
        text = run.get("text") or ""
        style = run.get("style") or {}
        font = _rich_run_font(ctx, run, data)
        for unit in _split_rich_text_units(text):
            if unit == "\n":
                lines.append(current or [{"text": "", "style": style, "font": font, "width": 0}])
                current, current_w = [], 0
                continue
            w = _run_text_width(font, unit)
            if current and current_w + w > max_width:
                lines.append(current)
                current, current_w = [], 0
            current.append({"text": unit, "style": style, "font": font, "width": w})
            current_w += w
    if current:
        lines.append(current)
    return lines


def _rich_line_metrics(line: list, default_font_size: int) -> tuple[int, int]:
    max_fs = default_font_size
    width = 0
    for seg in line:
        style = seg.get("style") or {}
        max_fs = max(max_fs, int(style.get("font_size") or default_font_size))
        width += int(seg.get("width") or 0)
    return width, max(30, int(max_fs * 1.45))


def _draw_rich_editor_line(canvas, draw, ctx: RenderContext, data: dict, line: list, x: int, y: int):
    cursor = x
    default_fs = int(data.get("font_size") or 31)
    _, line_h = _rich_line_metrics(line, default_fs)
    for seg in line:
        text = seg.get("text") or ""
        if not text:
            continue
        style = seg.get("style") or {}
        font = seg.get("font") or _rich_run_font(ctx, seg, data)
        fill = style.get("color") or _spec_text_color(data, ctx)
        w = int(seg.get("width") or _run_text_width(font, text))
        fs = int(style.get("font_size") or default_fs)
        if style.get("background"):
            try:
                draw.rounded_rectangle([cursor - 2, y + 2, cursor + w + 2, y + line_h - 4], radius=5, fill=style.get("background"))
            except Exception:
                pass
        # PIL 没有真正 italic 变体时，保持正体，避免锯齿变形；bold 由 display role 映射。
        draw.text((cursor, y), text, font=font, fill=fill)
        if style.get("underline"):
            uy = y + max(20, int(fs * 1.02))
            draw.line([(cursor, uy), (cursor + w, uy)], fill=fill, width=max(1, fs // 18))
        cursor += w


def _spec_render_editor_json_panel(canvas, y, ctx: RenderContext, data: dict, editor_json: dict):
    blocks = _editor_json_blocks(editor_json, data, ctx)
    if not blocks:
        return None
    pad = 44
    content_w = ctx.content_w - pad * 2
    paragraph_spacing = int(data.get("paragraph_spacing") if data.get("paragraph_spacing") is not None else 18)
    default_font_size = int(data.get("font_size") or 31)
    measured = []
    total_h = pad * 2
    for block in blocks:
        if block["type"] == "image":
            path, display_w, display_h = _spec_rich_image_box(block["meta"], content_w)
            measured.append({**block, "path": path, "display_w": display_w, "display_h": display_h})
            total_h += display_h + paragraph_spacing
        elif block["type"] == "image_row":
            row = []
            gap = 18
            for meta in block.get("items") or []:
                path, display_w, display_h = _spec_rich_image_box(meta, content_w)
                row.append({"path": path, "display_w": display_w, "display_h": display_h})
            natural_w = sum(x["display_w"] for x in row) + gap * max(0, len(row) - 1)
            if row and natural_w > content_w:
                scale = max(0.08, content_w / natural_w)
                for item in row:
                    item["display_w"] = max(1, int(item["display_w"] * scale))
                    item["display_h"] = max(1, int(item["display_h"] * scale))
            row_h = max((x["display_h"] for x in row), default=0)
            measured.append({**block, "row": row, "gap": gap, "display_h": row_h})
            total_h += row_h + paragraph_spacing
        else:
            lines = _wrap_rich_runs(block["runs"], ctx, data, content_w)
            line_metrics = [_rich_line_metrics(line, default_font_size) for line in lines]
            measured.append({**block, "lines": lines, "metrics": line_metrics})
            total_h += sum(h for _, h in line_metrics) + paragraph_spacing
    panel_h = max(90, total_h - paragraph_spacing)
    x0, x1 = ctx.content_x0, ctx.content_x1
    has_panel = data.get("panel_style") != "none"
    if has_panel:
        _spec_draw_panel(canvas, ctx, data, x0, y, x1, y + panel_h, fill=data.get("fill"))
    d = ImageDraw.Draw(canvas)
    cy = y + pad
    for block in measured:
        if block["type"] == "image":
            img = _spec_load_image(block["path"], (block["display_w"], block["display_h"]), mode=data.get("image_fit") or "contain", radius=18)
            align = block.get("meta", {}).get("align") or data.get("text_align") or "center"
            img_x = x0 + pad
            if align == "center":
                img_x = x0 + pad + (content_w - block["display_w"]) // 2
            elif align == "right":
                img_x = x0 + pad + content_w - block["display_w"]
            FX.paste_with_shadow(canvas, img, (img_x, cy), offset=(0, 6), blur=14, alpha=80)
            cy += block["display_h"] + paragraph_spacing
            continue
        if block["type"] == "image_row":
            row = block.get("row") or []
            gap = block.get("gap") or 18
            row_w = sum(x["display_w"] for x in row) + gap * max(0, len(row) - 1)
            align = block.get("align") or data.get("text_align") or "center"
            img_x = x0 + pad
            if align == "center":
                img_x = x0 + pad + max(0, (content_w - row_w) // 2)
            elif align == "right":
                img_x = x0 + pad + max(0, content_w - row_w)
            for item in row:
                img = _spec_load_image(item["path"], (item["display_w"], item["display_h"]), mode=data.get("image_fit") or "contain", radius=18)
                FX.paste_with_shadow(canvas, img, (img_x, cy), offset=(0, 6), blur=14, alpha=80)
                img_x += item["display_w"] + gap
            cy += block["display_h"] + paragraph_spacing
            continue
        align = block.get("align") or data.get("text_align") or "left"
        for line, (tw, lh) in zip(block["lines"], block["metrics"]):
            tx = x0 + pad
            if align == "center":
                tx = x0 + pad + (content_w - tw) // 2
            elif align == "right":
                tx = x0 + pad + content_w - tw
            _draw_rich_editor_line(canvas, d, ctx, data, line, tx, cy)
            cy += lh
        cy += paragraph_spacing
    ctx.reserve((x0, y, x1, y + panel_h))
    return y + panel_h

def render_spec_text_panel(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, data.get("module_title") or "文字模块")
    text = data.get("text") or data.get("content") or ""
    bullets = data.get("bullets") or []
    subsections = data.get("subsections") or []
    list_items = data.get("list_items") or []
    images = data.get("images") if isinstance(data.get("images"), list) else []
    content_html = data.get("content_html") or ""
    editor_json = data.get("editor_json") or data.get("content_editor_json") or None
    if isinstance(editor_json, dict):
        rendered = _spec_render_editor_json_panel(canvas, y, ctx, data, editor_json)
        if rendered is not None:
            return rendered
    pad = 44
    font_size = int(data.get("font_size") or 31)
    font_role = "display" if data.get("font_weight") == "bold" else "body"
    f_body = ctx.font(font_size, role=font_role)
    f_subtitle = ctx.font(max(28, min(42, font_size + 4)), role="display")
    content_w = ctx.content_w - pad * 2
    line_h = max(34, int(font_size * float(data.get("line_height") or 1.45)))
    paragraph_spacing = int(data.get("paragraph_spacing") if data.get("paragraph_spacing") is not None else 18)
    text_align = data.get("text_align") or "left"
    underline = data.get("text_decoration") == "underline"
    italic = data.get("font_style") == "italic"
    blocks = []
    rich_blocks = _spec_blocks_from_rich_html(str(content_html), f_body, content_w, images) if content_html else []
    if rich_blocks:
        blocks.extend(rich_blocks)
    elif bullets:
        for b in bullets:
            blocks.append(("body", _wrap_text("• " + str(b), f_body, content_w)))
    else:
        main_lines = _wrap_text_block(str(text), f_body, content_w) if text else []
        if main_lines:
            blocks.append(("body", main_lines))
    if isinstance(subsections, list):
        for sec in subsections:
            if not isinstance(sec, dict):
                continue
            st = str(sec.get("title") or "").strip()
            sb = str(sec.get("text") or "").strip()
            sec_images = sec.get("images") if isinstance(sec.get("images"), list) else []
            img_paths = [str((x.get("path") if isinstance(x, dict) else x) or "").strip() for x in sec_images]
            first_img = str(sec.get("image") or sec.get("image_path") or "").strip()
            if first_img:
                img_paths.insert(0, first_img)
            if st:
                blocks.append(("subtitle", _wrap_text(st, f_subtitle, content_w)))
            if sb:
                blocks.append(("body", _wrap_text_block(sb, f_body, content_w)))
            for img in [x for x in img_paths if x]:
                blocks.append(("image", [img]))
    if isinstance(list_items, list) and list_items:
        item_lines = []
        for item in list_items:
            if isinstance(item, dict):
                raw = item.get("text") or item.get("name") or ""
            else:
                raw = str(item)
            if raw.strip():
                item_lines.extend(_wrap_text("• " + raw.strip(), f_body, content_w))
        if item_lines:
            blocks.append(("body", item_lines))
    if not rich_blocks:
        for img_item in images:
            img_path = str((img_item.get("path") if isinstance(img_item, dict) else img_item) or "").strip()
            if img_path:
                blocks.append(("image", [{"path": img_path, "width_pct": 1.0}]))

    image_h = int(data.get("subsection_image_height") or 260)
    line_count = sum(len(lines) for kind, lines in blocks if kind != "image")
    image_heights = [(_spec_rich_image_box(lines[0], content_w)[2] if lines else image_h) for kind, lines in blocks if kind == "image"]
    block_gaps = max(0, len(blocks) - 1) * paragraph_spacing
    has_panel = data.get("panel_style") != "none"
    title_h = 0 if data.get("hide_inner_title") or title in {"", "文字模块"} else 58
    panel_h = pad * 2 + title_h + line_count * line_h + sum(image_heights) + block_gaps
    panel_h = max(panel_h, 90)
    x0, x1 = ctx.content_x0, ctx.content_x1
    if has_panel:
        _spec_draw_panel(canvas, ctx, data, x0, y, x1, y + panel_h, fill=data.get("fill"))
    cy = y + pad
    if title_h:
        cy = _spec_section_title(canvas, ctx, x0 + pad, y + 30, title, font_size=40)
    d = ImageDraw.Draw(canvas)
    body_color = _spec_text_color(data, ctx)
    highlight_color = data.get("highlight_color") or ctx.palette.get("accent_a", "#FBBF24")
    def _line_x(line: str, font) -> int:
        bb = font.getbbox(line)
        tw = bb[2] - bb[0]
        if text_align == "center":
            return x0 + pad + (content_w - tw) // 2
        if text_align == "right":
            return x0 + pad + content_w - tw
        return x0 + pad

    def _draw_rich_line(line: str, font, xy, fill: str):
        tx, ty = xy
        if italic:
            bb = font.getbbox(line)
            tw, th = max(1, bb[2] - bb[0]), max(1, bb[3] - bb[1] + 8)
            layer = Image.new("RGBA", (tw + 26, th + 8), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            ld.text((2 - bb[0], 2 - bb[1]), line, font=font, fill=fill)
            slant = 0.18
            layer = layer.transform((layer.width + int(th * slant), layer.height), Image.AFFINE, (1, -slant, 0, 0, 1, 0), resample=Image.BICUBIC)
            canvas.alpha_composite(layer, (tx, ty))
        else:
            d.text((tx, ty), line, font=font, fill=fill)
        if underline:
            bb = font.getbbox(line)
            tw = bb[2] - bb[0]
            uy = ty + max(24, int(font_size * 0.95))
            d.line([(tx, uy), (tx + tw, uy)], fill=fill, width=max(1, font_size // 18))

    for kind, lines in blocks:
        if kind == "image":
            path, display_w, display_h = _spec_rich_image_box(lines[0] if lines else {}, content_w)
            img = _spec_load_image(path, (display_w, display_h), mode=data.get("image_fit") or "contain", radius=18)
            img_x = x0 + pad
            if text_align == "center":
                img_x = x0 + pad + (content_w - display_w) // 2
            elif text_align == "right":
                img_x = x0 + pad + content_w - display_w
            FX.paste_with_shadow(canvas, img, (img_x, cy), offset=(0, 6), blur=14, alpha=80)
            cy += display_h + paragraph_spacing
            continue
        font = f_subtitle if kind == "subtitle" else f_body
        fill = highlight_color if kind == "subtitle" else body_color
        for line in lines:
            _draw_rich_line(line, font, (_line_x(line, font), cy), fill)
            cy += line_h
        cy += paragraph_spacing
    ctx.reserve((x0, y, x1, y + panel_h))
    return y + panel_h


def render_spec_image_grid(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "图片展示")
    images = data.get("images") or data.get("items") or []
    cols = int(data.get("columns") or (3 if len(images) != 4 else 2))
    cols = max(1, min(cols, 4))
    gap = 20
    pad = 38
    cell_w = (ctx.content_w - pad * 2 - gap * (cols - 1)) // cols
    cell_h = int(cell_w * float(data.get("aspect_ratio", 0.66)))
    rows = max(1, (len(images) + cols - 1) // cols)
    panel_h = 116 + rows * cell_h + (rows - 1) * gap + pad
    _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill"))
    cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=38)
    for idx, item in enumerate(images):
        path = item.get("path") if isinstance(item, dict) else item
        col, row = idx % cols, idx // cols
        x = ctx.content_x0 + pad + col * (cell_w + gap)
        yy = cy + row * (cell_h + gap)
        img = _spec_load_image(path, (cell_w, cell_h), mode=item.get("fit") if isinstance(item, dict) else data.get("image_fit", "contain"), radius=24)
        FX.paste_with_shadow(canvas, img, (x, yy), offset=(0, 8), blur=16, alpha=90)
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


def render_spec_image_text_split(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "图文模块")
    layout = data.get("layout") or data.get("layout_form") or "left_image_right_text"
    images = data.get("images") or []
    image_path = data.get("image") or data.get("image_path") or ((images[0].get("path") if isinstance(images[0], dict) else images[0]) if images else "")
    text = data.get("text") or data.get("content") or ""
    actions = data.get("actions") or []
    pad, gap = 42, 28
    horizontal = layout in ("left_image_right_text", "right_image_left_text")
    font_size = int(data.get("font_size") or 29)
    font_role = "display" if data.get("font_weight") == "bold" else "body"
    f = ctx.font(font_size, role=font_role)
    title_h = 78 if title else 0
    body_color = _spec_text_color(data, ctx)
    d = ImageDraw.Draw(canvas)
    if horizontal:
        panel_h = int(data.get("height", 520))
        _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill"))
        cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=38)
        img_w = int((ctx.content_w - pad * 2 - gap) * 0.42)
        txt_w = ctx.content_w - pad * 2 - gap - img_w
        img_h = panel_h - (cy - y) - pad
        img_x = ctx.content_x0 + pad if layout == "left_image_right_text" else ctx.content_x1 - pad - img_w
        txt_x = img_x + img_w + gap if layout == "left_image_right_text" else ctx.content_x0 + pad
        img = _spec_load_image(image_path, (img_w, img_h), mode=data.get("image_fit") or data.get("fit") or "contain", radius=28)
        FX.paste_with_shadow(canvas, img, (img_x, cy), offset=(0, 8), blur=18, alpha=100)
        yy = cy + 4
        for line in _wrap_text_block(str(text), f, txt_w):
            if yy > y + panel_h - 108:
                break
            d.text((txt_x, yy), line, font=f, fill=body_color)
            yy += max(40, int(font_size * 1.45))
        if actions:
            _spec_draw_action(canvas, ctx, (txt_x, y + panel_h - 86, txt_x + 260, y + panel_h - 30), actions[0])
    else:
        content_w = ctx.content_w - pad * 2
        lines = _wrap_text_block(str(text), f, content_w) if text else []
        line_h = max(40, int(font_size * 1.45))
        text_h = max(line_h if text else 0, len(lines) * line_h)
        requested_h = int(data.get("height", 0) or 0)
        max_img_h = max(220, min(520, requested_h - pad * 2 - title_h - text_h - gap if requested_h else 420))
        img_h = int(data.get("image_height") or max_img_h)
        img_h = max(180, min(img_h, max_img_h))
        action_h = 74 if actions else 0
        stack_gap = gap if text and image_path else 0
        panel_h = pad * 2 + title_h + img_h + stack_gap + text_h + action_h
        panel_h = max(280, panel_h)
        _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill"))
        cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=38)
        img = _spec_load_image(image_path, (content_w, img_h), mode=data.get("image_fit") or data.get("fit") or "contain", radius=28)
        if layout == "bottom_image_top_text":
            yy = cy
            for line in lines:
                d.text((ctx.content_x0 + pad, yy), line, font=f, fill=body_color)
                yy += line_h
            img_y = yy + stack_gap
            FX.paste_with_shadow(canvas, img, (ctx.content_x0 + pad, img_y), offset=(0, 8), blur=18, alpha=100)
        else:
            img_y = cy
            FX.paste_with_shadow(canvas, img, (ctx.content_x0 + pad, img_y), offset=(0, 8), blur=18, alpha=100)
            yy = img_y + img_h + stack_gap
            for line in lines:
                d.text((ctx.content_x0 + pad, yy), line, font=f, fill=body_color)
                yy += line_h
        if actions:
            _spec_draw_action(canvas, ctx, (ctx.content_x0 + pad, y + panel_h - pad - 64, ctx.content_x0 + pad + 260, y + panel_h - pad), actions[0])
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


def render_spec_rating_bars(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "课程评分")
    items = data.get("items") or []
    pad = 42
    row_h = 64
    panel_h = 118 + max(1, len(items)) * row_h + pad
    _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill", "#254981"))
    cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=38, accent="#F8C94A")
    d = ImageDraw.Draw(canvas)
    f_label = ctx.font(27, role="body")
    f_score = ctx.font(28, role="display")
    label_w = int(ctx.content_w * 0.45)
    bar_w = ctx.content_w - pad * 2 - label_w - 90
    for item in items:
        label = str(item.get("label") or item.get("name") or "")
        score = float(item.get("score") or item.get("value") or 0)
        max_score = float(item.get("max") or data.get("max_score") or 5)
        d.text((ctx.content_x0 + pad, cy + 6), label[:34], font=f_label, fill="#EEF4FF")
        bx = ctx.content_x0 + pad + label_w
        by = cy + 14
        d.rounded_rectangle([bx, by, bx + bar_w, by + 24], radius=12, fill=(120, 157, 224, 80))
        fill_w = int(bar_w * max(0, min(1, score / max_score)))
        d.rounded_rectangle([bx, by, bx + fill_w, by + 24], radius=12, fill="#5FA1FF")
        d.text((bx + bar_w + 24, cy + 2), f"{score:.2f}", font=f_score, fill="#FFFFFF")
        cy += row_h
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


def render_spec_action_bar(canvas, y, ctx: RenderContext, data: dict) -> int:
    """Standalone CTA/action element.

    For inline actions, other spec renderers call _spec_draw_action directly.
    This renderer covers module-external centered CTA blocks.
    """
    action = data.get("action") or data
    placement = action.get("placement") or data.get("placement") or "center"
    text = action.get("text") or data.get("text") or "立即报名"
    w = int(data.get("width", 360))
    h = int(data.get("height", 72))
    pad_top = int(data.get("pad_top", 22))
    pad_bottom = int(data.get("pad_bottom", 22))
    if placement.endswith("left"):
        x0 = ctx.content_x0
    elif placement.endswith("right"):
        x0 = ctx.content_x1 - w
    else:
        x0 = ctx.content_x0 + (ctx.content_w - w) // 2
    y0 = y + pad_top
    _spec_draw_action(canvas, ctx, (x0, y0, x0 + w, y0 + h), {**action, "text": text})
    ctx.reserve((x0, y0, x0 + w, y0 + h))
    return y + pad_top + h + pad_bottom


def render_spec_avatar_group_wall(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "人员展示")
    groups = data.get("submodules") or data.get("groups") or []
    speaker = data.get("speaker") or {}
    show_speaker = bool(speaker.get("name") or speaker.get("title") or speaker.get("avatar") or speaker.get("sections"))
    pad = 42
    bottom_pad = 28
    cols_default = int(data.get("columns", 3))
    avatar = int(data.get("avatar_size", 132))
    card_h = avatar + 76
    single_empty_group = len(groups) == 1 and not str(groups[0].get("title") or "").strip()
    f_body = ctx.font(24, role="body")
    text_parts = []
    for sec in speaker.get("sections") or []:
        if isinstance(sec, dict):
            text_parts.append(" ".join([str(sec.get("title") or "").strip(), str(sec.get("text") or "").strip()]).strip())
    speaker_text_w = max(120, ctx.content_w - pad * 2 - 28 * 2 - 250 - 24)
    speaker_lines = _wrap_text_block("\n".join([x for x in text_parts if x]) or "", f_body, speaker_text_w)
    speaker_text_h = len(speaker_lines) * 34
    speaker_h = 0
    if show_speaker:
        speaker_h = max(248, 28 + max(210, 92 + speaker_text_h) + 24)
    group_heights = []
    for g in groups:
        cols = int(g.get("columns", cols_default))
        rows = max(1, (len(g.get("items") or []) + cols - 1) // cols)
        heading_h = 0 if single_empty_group and not str(g.get("title") or "").strip() else 56
        group_heights.append(heading_h + rows * card_h + 24)
    panel_h = 118 + sum(group_heights) + ((8 + speaker_h) if show_speaker else 0) + bottom_pad
    _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill", "#392858"), outline=data.get("outline") or "#B676FF")
    cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=40, accent="#D276FF")
    d = ImageDraw.Draw(canvas)
    f_sub = ctx.font(30, role="display")
    f_name = ctx.font(24, role="display")
    f_org = ctx.font(22, role="body")
    for g in groups:
        sub_title = str(g.get("title") or "").strip()
        if sub_title:
            d.text((ctx.content_x0 + pad, cy), sub_title, font=f_sub, fill="#FFFFFF")
            cy += 56
        items = g.get("items") or []
        cols = int(g.get("columns", cols_default))
        cell_w = (ctx.content_w - pad * 2) // cols
        for i, item in enumerate(items):
            col, row = i % cols, i // cols
            cx = ctx.content_x0 + pad + col * cell_w + cell_w // 2
            ay = cy + row * card_h
            av = _spec_load_image(item.get("avatar") or item.get("image") or "", (avatar, avatar), mode="cover", radius=avatar // 2, fallback_label="头像")
            ring = Image.new("RGBA", (avatar + 12, avatar + 12), (0, 0, 0, 0))
            rd = ImageDraw.Draw(ring)
            rd.ellipse([0, 0, avatar + 11, avatar + 11], fill=(255, 255, 255, 235))
            rd.ellipse([3, 3, avatar + 8, avatar + 8], outline=hex_to_rgb(ctx.palette.get("accent_b", "#B676FF")) + (190,), width=4)
            ring.alpha_composite(av, (6, 6))
            canvas.alpha_composite(ring, (cx - (avatar + 12) // 2, ay))
            name = item.get("name") or item.get("display_name") or ""
            org = item.get("org") or item.get("title") or ""
            nb = f_name.getbbox(name[:22])
            d.text((cx - (nb[2] - nb[0]) // 2, ay + avatar + 18), name[:22], font=f_name, fill="#FFFFFF")
            ob = f_org.getbbox(org)
            d.text((cx - (ob[2] - ob[0]) // 2, ay + avatar + 52), org[:24], font=f_org, fill="#DDEBFF")
        rows = max(1, (len(items) + cols - 1) // cols)
        cy += rows * card_h + 24
    if show_speaker:
        cy += 8
        _frosted_panel(canvas, (ctx.content_x0 + pad, cy, ctx.content_x1 - pad, cy + speaker_h), radius=24, alpha=120, fill_hex=data.get("fill") or "#2C518E")
        sx = ctx.content_x0 + pad + 28
        sy = cy + 28
        photo = _spec_load_image(speaker.get("avatar") or "", (210, 210), mode="cover", radius=105, fallback_label="讲师")
        canvas.alpha_composite(photo, (sx, sy))
        tx = sx + 250
        f_sp_name = ctx.font(34, role="display")
        f_sp_title = ctx.font(25, role="body")
        d.text((tx, sy + 4), speaker.get("name") or "讲师姓名", font=f_sp_name, fill="#FFFFFF")
        d.text((tx, sy + 50), speaker.get("title") or "", font=f_sp_title, fill="#DDEBFF")
        yy = sy + 92
        for line in speaker_lines:
            if yy > cy + speaker_h - 40:
                break
            d.text((tx, yy), line, font=f_body, fill="#F4F7FF")
            yy += 34
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


def render_spec_quote_cards(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "学员之声")
    items = data.get("items") or data.get("quotes") or []
    cols = int(data.get("columns", 2))
    gap, pad = 22, 42
    card_w = (ctx.content_w - pad * 2 - gap * (cols - 1)) // cols
    card_h = int(data.get("card_height", 260))
    rows = max(1, (len(items) + cols - 1) // cols)
    panel_h = 118 + rows * card_h + (rows - 1) * gap + pad
    _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill", "#24477C"))
    cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=38, accent="#F8C94A")
    d = ImageDraw.Draw(canvas)
    f = ctx.font(25, role="body")
    f_name = ctx.font(24, role="display")
    for idx, item in enumerate(items):
        col, row = idx % cols, idx // cols
        x = ctx.content_x0 + pad + col * (card_w + gap)
        yy = cy + row * (card_h + gap)
        _frosted_panel(canvas, (x, yy, x + card_w, yy + card_h), radius=24, alpha=190, fill_hex="#385B9E")
        tx, ty = x + 28, yy + 24
        d.text((tx, ty), "“", font=ctx.font(54, role="display"), fill="#F8C94A")
        ty += 38
        for line in _wrap_text_block(str(item.get("text") or item.get("quote") or ""), f, card_w - 56):
            if ty > yy + card_h - 62:
                break
            d.text((tx, ty), line, font=f, fill="#F4F7FF")
            ty += 34
        author = item.get("author") or item.get("name") or ""
        d.text((tx, yy + card_h - 46), f"— {author}", font=f_name, fill="#DDEBFF")
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


def render_spec_course_card_list(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "课程介绍")
    items = data.get("items") or data.get("courses") or data.get("submodules") or []
    pad, gap = 42, 24
    card_h = int(data.get("card_height", 360))
    panel_h = 118 + len(items) * card_h + max(0, len(items) - 1) * gap + pad
    _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill", "#243D73"))
    cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=38)
    for idx, item in enumerate(items):
        layout = item.get("layout") or ("left_image_right_text" if idx % 2 == 0 else "right_image_left_text")
        sub = {
            **item,
            "title": item.get("title") or item.get("name"),
            "layout": layout,
            "height": card_h,
            "fill": "transparent",
            "panel_style": "none",
            "module_frame_mode": "none",
            "image_fit": item.get("image_fit") or data.get("image_fit") or "contain",
        }
        cy = render_spec_image_text_split(canvas, cy, ctx, sub) + gap
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return y + panel_h


def render_spec_feedback_story_flow(canvas, y, ctx: RenderContext, data: dict) -> int:
    title = _spec_title_value(data, "课程反馈")
    subs = data.get("submodules") or []
    pad, gap = 42, 24
    tmp_y = y + 118
    rendered = []
    for sub in subs:
        form = sub.get("layout_form") or sub.get("type")
        if form in ("horizontal_rating_bars", "rating_bars"):
            h = 118 + max(1, len(sub.get("items") or [])) * 64 + 32
        elif form in ("tilted_image_strip", "image_grid"):
            h = 360
        else:
            h = 520
        rendered.append((form, sub, h))
        tmp_y += h + gap
    panel_h = max(360, tmp_y - y + pad)
    _spec_draw_panel(canvas, ctx, data, ctx.content_x0, y, ctx.content_x1, y + panel_h, fill=data.get("fill", "#1F3F7B"), outline=data.get("outline") or "#4DA0FF")
    cy = _spec_section_title(canvas, ctx, ctx.content_x0 + pad, y + 28, title, font_size=40, accent="#F8C94A")
    for form, sub, _h in rendered:
        sub = dict(sub)
        sub.setdefault("title", sub.get("title") or "")
        if form in ("horizontal_rating_bars", "rating_bars"):
            cy = render_spec_rating_bars(canvas, cy, ctx, sub) + gap
        elif form in ("tilted_image_strip", "image_grid"):
            sub.setdefault("columns", 4)
            sub.setdefault("aspect_ratio", 0.55)
            cy = render_spec_image_grid(canvas, cy, ctx, sub) + gap
        else:
            sub.setdefault("layout", sub.get("layout") or "right_image_left_text")
            cy = render_spec_image_text_split(canvas, cy, ctx, sub) + gap
    ctx.reserve((ctx.content_x0, y, ctx.content_x1, y + panel_h))
    return max(cy, y + panel_h)
