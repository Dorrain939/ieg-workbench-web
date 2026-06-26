"""
长图海报渲染引擎 v2
====================

核心改造：
- 从 "A3 单图 + AI 满图" 改为 "1200 宽长图 + 模块化 sections 流式拼装"
- AI 只负责 hero_strip 中央插画 + 散点装饰素材，**绝不负责文字 / 渐变背景 / section 卡片**
- 所有文字、卡片、二维码框、装饰几何由 PIL 精准渲染

输入：brief JSON（schema_version=2，参见 references/brief-schema-v2.md）
输出：PNG（长图）+ PDF（300dpi 印刷）

v0.5 关键变化：
- 接入 palette_lab.get_scheme()：按 scene + scheme_id/vibe 选成熟配色方案
- 接入 copy_writer.auto_fill_brief()：brief 字段为空或 "AUTO" 时自动写文案
- _draw_background 支持 bg_image 路径：本地 PNG 优先 + 颜色统一滤镜 + 渐变遮罩 + grain
- 装饰 scatter 自动避开 ctx.occupied 禁飞区
"""
from __future__ import annotations
import argparse
import json
import pathlib
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from lib import components as C
from lib import decorations as D
from lib import effects as FX
from lib.context import RenderContext
from lib.palette import SCENE_PALETTE, hex_to_rgb
from lib.palette_lab import get_scheme
from lib.copy_writer import auto_fill_brief, DEFAULT_FIELDS

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

CANVAS_WIDTH_DEFAULT = 1200
MARGIN_X_RATIO = 0.07  # 1200 -> 84 px
SECTION_GAP = 56       # section 之间的固定间距（1200 宽下）
TITLE_TO_BODY_GAP = 0   # v0.9.10：小标题→正文间距全部内化进 render_section_title_bar（bar_h = nh + 18）。
                        # 这里保留 0，避免再叠加。改这个常量不会影响标题到正文的距离。
HERO_TO_TITLE_GAP = 0   # v0.9.9：hero（紧贴艺术字底，且 -30 进 hero 阴影区）→ 首个 numbered 标题；用户反馈"距离要砍到一半"

# Section type → 渲染函数（component contract: render(canvas, y, ctx, data) -> y_next）
RENDERERS = {
    "hero_strip":          C.render_hero_strip,
    "lead_paragraph":      C.render_lead_paragraph,
    "section_title_bar":   C.render_section_title_bar,
    "info_card":           C.render_info_card,
    "info_card_with_qr":   C.render_info_card_with_qr,
    "qa_block":            C.render_qa_block,
    "meta_row":            C.render_meta_row,
    "schedule_table":      C.render_schedule_table,
    "resource_grid":       C.render_resource_grid,
    "cta_button":          C.render_cta_button,
    "rules_box":           C.render_rules_box,
    "contact_card":        C.render_contact_card,
    "footer_logobar":      C.render_footer_logobar,
    # v0.9 新增（模块化拼装）
    "curriculum_timeline": C.render_curriculum_timeline,
    "faculty_grid":        C.render_faculty_grid,
    "benefit_grid":        C.render_benefit_grid,
    "notice_box":          C.render_notice_box,
    "contact_inline":      C.render_contact_inline,
    "bullet_points_block": C.render_bullet_points_block,
    # v0.9.4：透明 top/bottom logo 条
    "top_logo_bar":        C.render_top_logo_bar,
    # v0.10：通用表格组件（你给二维数据，引擎管列宽/wrap/表头/斑马纹）
    "data_table":          C.render_data_table,
    # v0.10.1：复杂表格组件（支持colspan/rowspan合并单元格）
    "complex_table":       C.render_complex_table,
    # v0.10.1：副标题文字（艺术字下方）
    "subtitle_text":       C.render_subtitle_text,
    # v0.10.2：Playwright 复杂表格插件（HTML→截图→paste）
    "table_module":        C.render_table_module_section,
    # v0.10.4：直接插入图片
    "image_block":         C.render_image_block,
    # v0.11：规格化版式能力
    "spec_text_panel":         C.render_spec_text_panel,
    "spec_image_grid":         C.render_spec_image_grid,
    "spec_image_text_split":   C.render_spec_image_text_split,
    "spec_action_bar":         C.render_spec_action_bar,
    "spec_rating_bars":        C.render_spec_rating_bars,
    "spec_avatar_group_wall":  C.render_spec_avatar_group_wall,
    "spec_quote_cards":        C.render_spec_quote_cards,
    "spec_course_card_list":   C.render_spec_course_card_list,
    "spec_feedback_story_flow": C.render_spec_feedback_story_flow,
}


def _measure_canvas_height(brief: dict) -> int:
    """先用 dry-run 估算总高，避免一次画布太大爆内存。

    简化策略：每个 section 给一个保守预估值，引擎流式追加；最终高度 = 累加 + 上下 padding。
    实际渲染时如有偏差，引擎会再做一次裁剪。
    """
    estimates = {
        "hero_strip":          900,
        "lead_paragraph":      360,
        "section_title_bar":   200,
        "info_card":           420,
        "info_card_with_qr":   500,
        "qa_block":            240 + 200 * len(brief.get("_qa_count_hint", [1, 2, 3])),
        "meta_row":            220,
        "schedule_table":      520,
        "resource_grid":       460,
        "cta_button":          280,
        "rules_box":           340,
        "contact_card":        540,
        "footer_logobar":      200,
        # v0.9
        "curriculum_timeline": 1200,
        "faculty_grid":        900,
        "benefit_grid":        520,
        "notice_box":          340,
        "contact_inline":      120,
        "bullet_points_block": 540,
        "data_table":          480,
        # v0.10.1
        "complex_table":       1400,
        # v0.10.1 subtitle_text
        "subtitle_text":       120,
        # v0.10.2 Playwright 表格插件（按每个 section 约 600px 估算）
        "table_module":        600,
        # v0.11 spec renderers
        "spec_text_panel":          520,
        "spec_image_grid":          760,
        "spec_image_text_split":    620,
        "spec_action_bar":          140,
        "spec_rating_bars":         520,
        "spec_avatar_group_wall":   1500,
        "spec_quote_cards":         760,
        "spec_course_card_list":    1200,
        "spec_feedback_story_flow": 1800,
        "image_block":              520,
    }
    total = 120  # top padding
    for s in brief.get("sections", []):
        if s["type"] == "qa_block":
            total += 240 + 200 * len(s.get("items", []))
        else:
            total += estimates.get(s["type"], 300)
        total += SECTION_GAP
    total += 160  # bottom padding
    return max(total, 2400)


def _scatter_bg_decorations(canvas: Image.Image, cfg: dict, w: int, h: int):
    """在背景层（L1.5）撒装饰素材：贴在全局渐变之上，但会被后续 sections 盖住。
    不检查禁飞区，全幅均匀分布；带 alpha 控制让装饰偏暗与底图融合。

    cfg 字段：
      types: List[{path, size: [min,max], count, alpha, rotate, blur}]
      seed: int
      exclude_top / exclude_bottom: 顶部/底部留白
    """
    import random as _r
    rng = _r.Random(cfg.get("seed", 42))
    top_pad = int(cfg.get("exclude_top", 60))
    bot_pad = int(cfg.get("exclude_bottom", 100))
    types = cfg.get("types", [])

    placed = []  # (x, y, size) 用于互斥避免重叠
    for t in types:
        path = t.get("path")
        if not path or not pathlib.Path(path).exists():
            continue
        try:
            base = Image.open(path).convert("RGBA")
        except Exception as e:
            print(f"[bg_deco] 加载失败 {path}: {e}")
            continue
        cnt = int(t.get("count", 8))
        smin, smax = t.get("size", [60, 120])
        smin, smax = int(smin), int(smax)
        alpha_pct = float(t.get("alpha", 1.0))  # 0-1
        rotate = bool(t.get("rotate", False))
        blur_r = float(t.get("blur", 0))

        attempts = 0
        max_attempts = cnt * 25
        for _ in range(cnt):
            placed_this = False
            while attempts < max_attempts and not placed_this:
                attempts += 1
                size = rng.randint(smin, smax)
                x = rng.randint(20, w - size - 20)
                y = rng.randint(top_pad, h - bot_pad - size)
                # 与已放置的装饰避让（让它们不堆叠）
                conflict = False
                for px, py, ps in placed:
                    if abs(x - px) < max(80, (size + ps) // 2) and \
                       abs(y - py) < max(80, (size + ps) // 2):
                        conflict = True
                        break
                if conflict:
                    continue
                # 缩放
                ratio = size / max(base.size)
                new_size = (max(8, int(base.width * ratio)),
                            max(8, int(base.height * ratio)))
                im = base.resize(new_size, Image.LANCZOS)
                if rotate:
                    im = im.rotate(rng.randint(-25, 25),
                                   resample=Image.BICUBIC, expand=True)
                if blur_r > 0:
                    from PIL import ImageFilter as _IF
                    im = im.filter(_IF.GaussianBlur(radius=blur_r))
                if alpha_pct < 1.0:
                    a = im.split()[-1].point(lambda p: int(p * alpha_pct))
                    im.putalpha(a)
                canvas.alpha_composite(im, (x, y))
                placed.append((x, y, size))
                placed_this = True


def _draw_background(canvas: Image.Image, brief: dict):
    """海报背景渲染 · 四层图层架构（🔒 v0.10.4 铁律，顺序不可乱）

    ┌─────────────────────────────────────────────────────────────────┐
    │  Layer 4：顶部 Logo 横幅（top_logo_bar section）                │ ← 最顶层（由 sections 流式渲染，不在此函数处理）
    │  Layer 3：艺术字（hero_strip.title_card，chroma_key 抠黑底）    │ ← 由 render_hero_strip 处理
    │  Layer 2：头部底图（canvas.bg_image_path）                      │ ← 本函数 L0 阶段处理
    │             宽度 = 1440px，底部强制渐变到背景色                  │
    │  Layer 1：全局底图（canvas.bg_colors 渐变）                     │ ← 本函数 L1 阶段处理，铺满整张海报
    └─────────────────────────────────────────────────────────────────┘

    渲染顺序：
      L1 全局底图（bg_colors 渐变，铺满整张海报）
      L0 头部底图（bg_image_path，宽度=画布宽，高度由比例决定）
         └─ 底部立即叠渐变遮罩（bg_image_bottom_fade，锚定底图底边）
      L0.5 头部底图颜色统一滤镜 + 顶部渐变（可选）
      L2~L4 由 _draw_background 之外的 sections 流式渲染完成

    canvas_cfg.bg_image_path : str  头部底图路径（必须是 1440px 宽的横版图）
    canvas_cfg.bg_image_tint : str  颜色统一滤镜色值，默认不叠加
    canvas_cfg.bg_image_tint_alpha : 0-255  滤镜强度，默认 80
    canvas_cfg.bg_image_top_fade   : 0-255  顶部渐变强度，默认 0
    canvas_cfg.bg_image_bottom_fade: 0-255  底部渐变强度，默认 180（🔒 最小 60，不可为 0）
    """
    canvas_cfg = brief.get("canvas", {})
    strategy = canvas_cfg.get("bg_strategy", "gradient-2")
    w, h = canvas.size

    bg_image_path = canvas_cfg.get("bg_image_path")
    use_bg_image = bool(bg_image_path) and pathlib.Path(bg_image_path).exists()

    def _paint_global_base():
        """Paint L1: global background image when provided, otherwise palette gradient."""
        global_bg_path = canvas_cfg.get("global_bg_path")
        if global_bg_path and pathlib.Path(global_bg_path).exists():
            try:
                bg_full = Image.open(global_bg_path).convert("RGBA")
                ratio = max(w / bg_full.width, h / bg_full.height)
                scaled = bg_full.resize((max(1, int(bg_full.width * ratio)), max(1, int(bg_full.height * ratio))), Image.LANCZOS)
                left = max(0, (scaled.width - w) // 2)
                top = max(0, (scaled.height - h) // 2)
                bg = scaled.crop((left, top, left + w, top + h))
                canvas.paste(bg.convert("RGB"), (0, 0))
                canvas_cfg["_global_bg_actual_size"] = [bg_full.width, bg_full.height]
                return
            except Exception as e:
                print(f"[warn] global_bg 加载失败，回退渐变: {e}")
        if strategy == "solid":
            color = canvas_cfg.get("bg_colors", ["#1A4FE0"])[0]
            r, g, b = hex_to_rgb(color)
            canvas.paste((r, g, b), (0, 0, w, h))
        else:
            c1, c2 = canvas_cfg.get("bg_colors", ["#5B3FA0", "#3B2F8A"])
            grad = FX.linear_gradient((w, h), c1, c2, "vertical")
            canvas.paste(grad.convert("RGB"), (0, 0))

    # ---------- L0: AI 底图（如果有） ----------
    # v0.8.1：AI 主视觉插画通常用作"hero 顶部装饰"，不应该铺满整个长海报。
    # 新增 bg_image_height（单位 px，默认 760，等于 hero_strip 高度）+
    # bg_image_crop_top（0~1，从原图顶部裁掉的比例，去掉空天空）。
    # v0.9.1：新增 bg_image_fit = "cover" | "contain" | "width"
    #   width    （新默认）：按 1200 宽缩放，高度顺延，不裁红包/主体；
    #   cover                ：旧逻辑，可能裁掉
    #   contain              ：完整放进去，上下补 bg_colors
    if use_bg_image:
        try:
            bg_full = Image.open(bg_image_path).convert("RGBA")
            # 顶部裁掉空白/空天空
            crop_top = float(canvas_cfg.get("bg_image_crop_top", 0.0))
            crop_bottom = float(canvas_cfg.get("bg_image_crop_bottom", 0.0))
            cy0 = int(bg_full.height * max(0.0, min(0.9, crop_top))) if crop_top > 0 else 0
            cy1 = bg_full.height - int(bg_full.height * max(0.0, min(0.9, crop_bottom))) if crop_bottom > 0 else bg_full.height
            if cy1 - cy0 < 50:
                cy0, cy1 = 0, bg_full.height
            bg_full = bg_full.crop((0, cy0, bg_full.width, cy1))

            target_band_h = int(canvas_cfg.get("bg_image_height", 760))
            target_band_h = max(200, min(target_band_h, h))
            fit_mode = canvas_cfg.get("bg_image_fit", "width")
            # 🔒 铁律 v0.10.3：bg_image_fit 强制为 "width"，底图必须与画布同宽。
            # 无论 brief 填 "cover" / "contain"，引擎均忽略并强制走 "width" 逻辑。
            fit_mode = "width"

            # 先把整张画布铺成 L1 全局底图（或渐变兜底），再贴 L2 头部底图
            _paint_global_base()

            # v0.9.2：bg_image_chroma_key —— 把 AI 装饰图的纯色背景抠透明，
            #   让底层 base_grad 的明亮渐变透出来，避免"灰色装饰图底"
            need_bg_key = bool(canvas_cfg.get("bg_image_chroma_key", False))
            if need_bg_key:
                bg_full = FX.chroma_key_to_alpha(
                    bg_full,
                    bg_kind=canvas_cfg.get("bg_image_chroma_bg_kind", "auto"),
                    bg_lightness_min=int(canvas_cfg.get("bg_image_chroma_light_min", 140)),
                    bg_darkness_max=int(canvas_cfg.get("bg_image_chroma_dark_max", 95)),
                    bg_saturation_max=int(canvas_cfg.get("bg_image_chroma_sat_max", 50)),
                    softness=int(canvas_cfg.get("bg_image_chroma_softness", 40)),
                    edge_clean=True,
                )

            def _place_bg(bg_img, x, y):
                """把 bg_img 贴到 canvas 上（in-place，因为 canvas 是外层传入对象）。
                RGBA 走 alpha_composite（保留透明），RGB 走 paste。
                注意：不能 `canvas = ...` 重新赋值，那会让外层调用拿不到。
                """
                if bg_img.mode == "RGBA":
                    # canvas 是 RGB，先临时升 RGBA 合成再写回
                    tmp = canvas.convert("RGBA")
                    tmp.alpha_composite(bg_img, (x, y))
                    # paste 回原 canvas（in-place 修改像素）
                    canvas.paste(tmp.convert("RGB"), (0, 0))
                else:
                    canvas.paste(bg_img.convert("RGB"), (x, y))

            # 🔒 铁律 v0.10.4：头部底图从 y=0 开始，与海报最顶部平齐。
            # logo 横幅浮在底图上方（由 sections 流式渲染保证图层顺序），
            # 不再把头部底图下移 logo 高度——下移会导致顶部出现纯色空白条。
            # bg_y_offset 固定为 0；logo_reserved_top 仅用于记录 hero_strip 偏移参考。
            logo_reserved_top = 0
            top_bar_section = next((s for s in brief.get("sections", []) if s.get("type") == "top_logo_bar"), None)
            if top_bar_section:
                _lh_arr = top_bar_section.get("logo_heights") or []
                _lh = max(int(h) for h in _lh_arr) if _lh_arr else int(top_bar_section.get("logo_height", 76))
                _pt = int(top_bar_section.get("pad_top", 24))
                _pb = int(top_bar_section.get("pad_bottom", 24))
                logo_reserved_top = _lh + _pt + _pb + 8
            elif (brief.get("logo_position") == "top" and brief.get("logos")):
                logo_reserved_top = int(brief.get("logo_height", 76)) + 48 + 24
            # 头部底图始终从 y=0 开始，不受 logo 高度影响
            bg_y_offset = 0

            # 🔒 铁律 v0.10.3：底图按画布宽度等比缩放，高度完全由原图比例决定。
            ratio = w / bg_full.width
            scaled_h = int(bg_full.height * ratio)
            bg = bg_full.resize((w, scaled_h), Image.LANCZOS)

            # 🔒 铁律 v0.10.4：头部底图底部渐变到透明（alpha 0），让全局底图透出。
            # 渐变区域 = 底图高度的 30%（最小 120px），从完全不透明渐变到完全透明。
            # 实现：在底图贴到 canvas 之前，先给底图本身底部叠加 alpha 渐变遮罩。
            fade_ratio = float(canvas_cfg.get("bg_image_bottom_fade_ratio", 0.30))
            fade_band_h = max(int(scaled_h * fade_ratio), 120)
            fade_band_h = min(fade_band_h, scaled_h)
            # 给底图底部区域做 alpha 渐变：顶部 alpha=255（不透明），底部 alpha=0（全透明）
            bg_rgba = bg.convert("RGBA")
            alpha_ch = bg_rgba.split()[3].copy()
            from PIL import ImageDraw as _ID
            fade_draw = _ID.Draw(alpha_ch)
            fade_start = scaled_h - fade_band_h
            for i in range(fade_band_h):
                # alpha 从 255 线性降到 0（越往下越透明）
                a = int(255 * (1.0 - i / fade_band_h))
                fade_draw.line([(0, fade_start + i), (w, fade_start + i)], fill=a)
            bg_rgba.putalpha(alpha_ch)
            bg = bg_rgba  # 替换为带透明底的版本
            _place_bg(bg, 0, bg_y_offset)

            target_band_h = scaled_h + bg_y_offset
            canvas_cfg["_ai_bg_actual_h"] = target_band_h
        except Exception as e:
            print(f"[warn] bg_image 加载失败，回退渐变: {e}")
            use_bg_image = False

    # ---------- L1: base 填充（无 AI 头图时） ----------
    if not use_bg_image:
        _paint_global_base()

    canvas_rgba = canvas.convert("RGBA") if canvas.mode != "RGBA" else canvas

    # ---------- L0.5: AI 图颜色统一滤镜（保色但收颜色） ----------
    if use_bg_image:
        tint = canvas_cfg.get("bg_image_tint")
        tint_alpha = canvas_cfg.get("bg_image_tint_alpha", 80)
        if tint:
            r, g, b = hex_to_rgb(tint)
            tint_layer = Image.new("RGBA", (w, h), (r, g, b, tint_alpha))
            canvas_rgba.alpha_composite(tint_layer)

        # 顶部渐变遮罩（可选）
        top_fade = canvas_cfg.get("bg_image_top_fade", 0)
        c1, c2 = canvas_cfg.get("bg_colors", ["#1A2A6C", "#0B1340"])
        if top_fade > 0:
            mask_h = max(int(h * 0.3), 200)
            r1, g1, b1 = hex_to_rgb(c1)
            for i in range(mask_h):
                a = int(top_fade * (1 - i / mask_h))
                ImageDraw.Draw(canvas_rgba).line(
                    [(0, i), (w, i)], fill=(r1, g1, b1, a))
        # 注意：底部渐变已在 L0 阶段贴底图后立即完成，此处不再重复处理

    # ---------- L1.5: 底层装饰（嵌入背景层，会被后续 sections 卡片/文字盖住） ----------
    bg_deco = brief.get("background_decorations")
    if bg_deco:
        _scatter_bg_decorations(canvas if canvas.mode == "RGBA" else canvas_rgba,
                                bg_deco, w, h)

    # ---------- L2: 径向光晕（让上下有"光线" ----------
    if canvas_cfg.get("glow", True):
        glow_a = canvas_cfg.get("glow_top_color") or "#FBBF24"
        glow_b = canvas_cfg.get("glow_bottom_color") or canvas_cfg.get("bg_colors", ["#5B3FA0"])[0]
        # 顶部光晕（限高，避免拖慢）
        top_glow = FX.radial_glow(
            (w, min(h, 1200)), (w // 2, 240), radius=int(w * 0.7),
            color=glow_a, alpha_center=70 if not use_bg_image else 50)
        canvas_rgba.alpha_composite(top_glow, (0, 0))
        # 底部光晕
        if h > 1500:
            bot_glow = FX.radial_glow(
                (w, 900), (w // 2, 700), radius=int(w * 0.6),
                color=glow_b, alpha_center=80 if not use_bg_image else 60)
            canvas_rgba.alpha_composite(bot_glow, (0, h - 900))

    # ---------- L3: 网格 / 底纹（可选） ----------
    pattern = canvas_cfg.get("pattern")  # "grid" | "dots" | None
    if pattern == "grid":
        d = ImageDraw.Draw(canvas_rgba)
        step = 48
        line_color = (255, 255, 255, 14)
        for x in range(0, w, step):
            d.line([(x, 0), (x, h)], fill=line_color, width=1)
        for y in range(0, h, step):
            d.line([(0, y), (w, y)], fill=line_color, width=1)
    elif pattern == "dots":
        d = ImageDraw.Draw(canvas_rgba)
        step = 36
        dot_color = (255, 255, 255, 28)
        for y in range(0, h, step):
            for x in range(0, w, step):
                d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=dot_color)

    # ---------- L4: 噪点 grain（v0.9.5 默认彻底关闭） ----------
    # 用户 2026-05-20 反馈：BILINEAR 颗粒仍呈砂纸感马赛克。
    # 决策：彻底删除噪点。除非 brief 显式 grain=true 且 grain_strength>0，否则跳过。
    if canvas_cfg.get("grain", False) and canvas_cfg.get("grain_strength", 0) > 0:
        grain = FX.fast_noise_grain(
            (w, h), strength=int(canvas_cfg["grain_strength"]),
            seed=brief.get("seed", 42), scale=2,
        )
        canvas_rgba.alpha_composite(grain)

    # 把 canvas 内容刷回（如果传入是 RGB）
    if canvas.mode != "RGBA":
        canvas.paste(canvas_rgba.convert("RGB"))
    else:
        canvas.alpha_composite(canvas_rgba, (0, 0))


def _apply_scheme(brief: dict) -> dict:
    """v0.5: 按 brief.scene + brief.scheme_id / brief.vibe 选成熟配色方案，
    把方案的 bg_colors / glow / pattern / palette 字段反写回 brief（仅当用户没显式指定时）。

    优先级：用户显式指定 > scheme 给的值 > 旧 SCENE_PALETTE 兜底。

    v0.9 新增：canvas.palette_strategy="named:<scheme_id>" 命名直选；
              "named:festival_red" / "named:deep_space" 等友好别名也会映射。
    """
    scene = brief.get("scene", "S1")
    scheme_id = brief.get("scheme_id")
    vibe = brief.get("vibe") or []

    # ---- v0.9: palette_strategy 命名直选 ----
    canvas_cfg = dict(brief.get("canvas") or {})
    strat = canvas_cfg.get("palette_strategy")
    if strat and isinstance(strat, str) and strat.startswith("named:"):
        named = strat.split(":", 1)[1].strip()
        # 友好别名：把无 scene 前缀的名字映射到 scheme_id
        named_alias = {
            "aurora":         ("S1", "S1-aurora"),
            "pixel_dawn":     ("S1", "S1-pixel-dawn"),
            "nebula_blue":    ("S1", "S1-nebula-blue"),
            "deep_space":     ("S2", "S2-deep-space"),
            "charcoal_gold":  ("S2", "S2-charcoal-gold"),
            "cyber_neon":     ("S3", "S3-cyber-neon"),
            "engine_core":    ("S3", "S3-engine-core"),
            "carnival":       ("S4", "S4-carnival"),
            "sunset_arcade":  ("S4", "S4-sunset-arcade"),
            "jubilee_red":    ("S4", "S4-jubilee-red"),
            "velvet_gold":    ("S5", "S5-velvet-gold"),
            "ink_honor":      ("S5", "S5-ink-honor"),
            "arena":          ("S6", "S6-arena"),
            "circuit_flame":  ("S6", "S6-circuit-flame"),
            # 新春/喜庆专用别名 → 走 S4 朱红暖金（明亮）。
            # 历史 v0.9 早期版本曾把 festival_red 映射到 S5-velvet-gold(酒红浮金)，
            # 实测过暗。v0.9.2 起改为 S4-jubilee-red：米白→暖橙底 + 中国红 accent。
            "festival_red":   ("S4", "S4-jubilee-red"),
        }
        if named in named_alias:
            scene, scheme_id = named_alias[named]
        else:
            # 直接当 scheme_id（带前缀如 "S5-velvet-gold"）
            scheme_id = named

    scheme = get_scheme(scene, scheme_id=scheme_id, vibe_keywords=vibe)
    print(f"[scheme] scene={scene} → {scheme.id} ({scheme.name}) — {scheme.theory}")

    # 1) canvas 背景层：仅在用户没显式给时使用 scheme 默认
    scheme_canvas = scheme.to_canvas_cfg()
    for k, v in scheme_canvas.items():
        canvas_cfg.setdefault(k, v)
    brief["canvas"] = canvas_cfg

    # 2) palette：scheme 给的 + brief.palette_override 覆盖
    palette = dict(SCENE_PALETTE.get(scene, SCENE_PALETTE["S1"]))   # 旧色板做兜底
    palette.update(scheme.to_palette_dict())                         # 新 scheme 覆盖
    palette.update(brief.get("palette_override") or {})              # 用户显式覆盖
    brief["_resolved_palette"] = palette
    brief["_resolved_bg_base"] = scheme.bg_colors[0]
    # v0.9.3：透传 brightness，所有信息卡组件读 _resolved_brightness 决定浅底/深底
    bri = (canvas_cfg.get("brightness")
           or getattr(scheme, "brightness", None)
           or "dark")
    canvas_cfg["_resolved_brightness"] = bri
    # 记录 scheme.brightness 与解析结果，便于后续观察
    brief["_resolved_brightness"] = bri
    return brief


def compose_long_poster(brief: dict, out_path: str) -> tuple[str, str]:
    """长图海报主渲染入口。

    🔒 v0.10.4 四层图层架构说明（AI 执行时必须严格遵守）：
    ─────────────────────────────────────────────────────
    在调用本函数渲染之前，AI 必须已完成以下生图步骤：

    步骤 1：用 ImageGen 生成 全局底图（L1）
            size=1440x2400, 竖版背景图, 不含文字
            → 存入 canvas.bg_colors 渐变（或后续扩展 global_bg_path）

    步骤 2：用 ImageGen 生成 头部底图（L2）
            size=1440x800（宽度必须=1440px）, 横版主视觉图
            → 存入 canvas.bg_image_path
            → 引擎自动缩放宽度 + 底部渐变遮罩（bg_image_bottom_fade）

    步骤 3：用 ImageGen 生成 艺术字主标题（L3）
            size=1440x400, 纯黑底（#000000），不透明
            → 存入 hero_strip.title_card.image
            → brief 必须设 chroma_key=true, chroma_bg_kind="dark", key_lightness=35

    步骤 4（可选）：用 ImageGen 生成 艺术字副标题（L3）
            size=1440x200, 纯黑底
            → 存入 subtitle_text 或第二个 hero_strip title_card

    步骤 5：sections[0] 必须是 top_logo_bar（L4，始终在最顶层）

    渲染顺序由本函数保证：
    _draw_background → L1全局底图 → L2头部底图+底部渐变
    sections 流式 → L4 top_logo_bar → L3 hero_strip艺术字 → 正文...
    ─────────────────────────────────────────────────────
    """
    # ---------- v0.5 step 0: 选 scheme + 自动补文案 ----------
    brief = _apply_scheme(brief)
    auto_fields = brief.get("auto_fields") or {}
    if auto_fields or brief.get("auto_fill", False):
        # 用 brief.auto_fields 合并 DEFAULT_FIELDS 喂 copy_writer
        fields = dict(DEFAULT_FIELDS)
        fields.update(auto_fields)
        before_n = sum(1 for s in brief.get("sections", [])
                       if (s.get("text") in (None, "", "AUTO")
                           or s.get("body") in (None, "", "AUTO")))
        brief = auto_fill_brief(brief, fields)
        print(f"[copy_writer] auto_fill 处理 {before_n} 处空字段")

    width = brief.get("canvas", {}).get("width", CANVAS_WIDTH_DEFAULT)
    height = _measure_canvas_height(brief)

    canvas = Image.new("RGB", (width, height), "#3B2F8A")
    _draw_background(canvas, brief)
    canvas = canvas.convert("RGBA")

    # 准备渲染上下文（使用 _apply_scheme 解析后的 palette）
    palette = brief["_resolved_palette"]
    ctx = RenderContext(
        canvas_size=canvas.size,
        margin_x=int(width * MARGIN_X_RATIO),
        palette=palette,
        decoration_family=brief.get("decoration_family", "semi-3d-collage"),
        font_path=(ASSETS / "fonts" / "TencentSans-W3.ttf"
                   if (ASSETS / "fonts" / "TencentSans-W3.ttf").exists()
                   else ASSETS / "fonts" / "font_gaming_bold.ttf"),
        font_path_display=(ASSETS / "fonts" / "TencentSans-W7.ttf"
                           if (ASSETS / "fonts" / "TencentSans-W7.ttf").exists()
                           else None),
        bg_base_color=brief.get("_resolved_bg_base", "#0F0A2E"),
        canvas_cfg=brief.get("canvas") or {},
    )

    # Section 流
    # v0.9.4 铁律：logo 不占模块槽，仅在最顶或最底以 top_logo_bar 形式出现，与其它元素零重叠。
    sections = list(brief.get("sections", []))
    logo_pos = brief.get("logo_position", "auto")  # top | bottom | none | auto
    brief_logos = brief.get("logos") or []
    logo_sections = [s for s in sections if s.get("type") == "top_logo_bar"]
    non_logo_sections = [s for s in sections if s.get("type") != "top_logo_bar"]
    if logo_sections and logo_pos == "top":
        sections = logo_sections[:1] + non_logo_sections
    elif logo_sections and logo_pos == "bottom":
        sections = non_logo_sections + logo_sections[:1]

    # v0.9.4：当 logo_position=top 时，从 y=0 开始（top_logo_bar 自带 pad_top），
    #         其余情况保持 100 留白。
    # v0.10.4：sections 里显式写了 top_logo_bar 时也从 y=0 开始。
    _has_top_bar_section = bool(sections and sections[0].get("type") == "top_logo_bar")
    y = 0 if (_has_top_bar_section or (brief.get("logo_position") == "top" and brief.get("logos"))) else 100

    has_hero_logo = any(s.get("type") == "hero_strip" and s.get("logo_slot") for s in sections)
    has_top_bar = any(s.get("type") == "top_logo_bar" for s in sections)
    has_footer = any(s.get("type") in ("footer_logobar", "top_logo_bar") and s != sections[0]
                     for s in sections)
    if logo_pos == "top" and not has_hero_logo and not has_top_bar and brief_logos:
        sections = [{
            "type": "top_logo_bar",
            "logos": brief_logos,
            "logo_height": brief.get("logo_height", 76),
            "gap": brief.get("logo_gap", 80),
            "align": brief.get("logo_align", "center"),
            "distribution": "even",
        }] + sections

    for idx, section in enumerate(sections):
        renderer = RENDERERS.get(section["type"])
        if not renderer:
            print(f"[warn] 未知 section type={section['type']}，跳过")
            continue
        try:
            y = renderer(canvas, y, ctx, section)
        except Exception as e:
            print(f"[error] 渲染 {section['type']} 失败：{e}")
            raise
        # v0.9.6：section_title_bar 后面紧跟非 title 的正文 → 紧凑间距，
        # 让小标题与其正文视觉成一组；其它情况维持 SECTION_GAP。
        # v0.9.7：hero_strip → 紧跟 section_title_bar 时收紧成 HERO_TO_TITLE_GAP，
        # 修『艺术字离正文太远』的视觉断层。
        next_section = sections[idx + 1] if idx + 1 < len(sections) else None
        if (section.get("type") == "section_title_bar"
                and next_section
                and next_section.get("type") != "section_title_bar"):
            y += TITLE_TO_BODY_GAP
        elif (section.get("type") == "hero_strip"
                and next_section
                and next_section.get("type") == "section_title_bar"):
            y += HERO_TO_TITLE_GAP
        elif (section.get("type") == "hero_strip"
                and next_section
                and next_section.get("type") == "subtitle_text"):
            # hero → subtitle 紧贴
            y += 0
        elif (section.get("type") == "subtitle_text"
                and next_section
                and next_section.get("type") == "section_title_bar"):
            # subtitle 之后接首个 section_title_bar：用紧凑间距，避免视觉断层
            y += HERO_TO_TITLE_GAP
        else:
            y += SECTION_GAP

    # v0.9.4: logo_position=bottom → 末尾插透明 top_logo_bar（同组件，仅是位置不同）
    has_bottom_bar = any(s.get("type") in ("footer_logobar", "top_logo_bar")
                         for s in sections[1:])
    if logo_pos == "bottom" and not has_bottom_bar and brief_logos:
        try:
            y = C.render_top_logo_bar(canvas, y, ctx, {
                "logos": brief_logos,
                "logo_height": brief.get("logo_height", 76),
                "gap": brief.get("logo_gap", 80),
                "align": brief.get("logo_align", "center"),
                "distribution": "even",
                "pad_top": 40,
                "pad_bottom": 40,
            })
            y += SECTION_GAP
        except Exception as e:
            print(f"[warn] 自动补底部 logo 失败：{e}")

    # 撒散点装饰（最上层）
    # v0.9.10：默认关闭（用户反馈"小方块小圆点很丑"）。
    # 仅当 brief.decorations 显式存在且 density != "none" 时才撒，
    # 真实装饰素材交给 hero_image / hero_mascot / 用户上传的 PNG，
    # 引擎不再凭空画几何占位。
    deco_cfg = brief.get("decorations")
    if deco_cfg and deco_cfg.get("density", "none") not in ("none", None, "off", False):
        D.scatter(canvas, ctx, deco_cfg)

    # 裁剪到实际使用高度（最后一个 section 的 y 位置 + bottom padding）
    final_h = min(y + 100, height)
    if final_h < height:
        canvas = canvas.crop((0, 0, width, final_h))

    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, format="PNG", optimize=True)
    pdf_path = out_path.replace(".png", ".pdf")
    canvas.convert("RGB").save(pdf_path, format="PDF", resolution=300)
    return out_path, pdf_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    brief = json.loads(pathlib.Path(args.brief).read_text(encoding="utf-8"))
    out = args.out or f"output/long_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    if not pathlib.Path(out).is_absolute():
        out = str(ROOT / out)

    png, pdf = compose_long_poster(brief, out)
    print(json.dumps({"png": png, "pdf": pdf}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
