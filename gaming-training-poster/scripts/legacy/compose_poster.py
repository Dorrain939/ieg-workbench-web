"""
Stage 2: 在底图上精准合成文字、Logo、二维码、装饰组件。
所有关键信息都走这里——不依赖 AI 写中文。
"""
from __future__ import annotations
import os, json, pathlib, argparse
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# 占位色板：与 design-system.md 保持一致
SCENE_PALETTE = {
    "S1": {"primary": "#3B82F6", "accent_a": "#FBBF24", "accent_b": "#10B981", "neutral": "#0F172A"},
    "S2": {"primary": "#1E1B4B", "accent_a": "#C9A961", "accent_b": "#475569", "neutral": "#0B1020"},
    "S3": {"primary": "#0F172A", "accent_a": "#22D3EE", "accent_b": "#A78BFA", "neutral": "#020617"},
    "S4": {"primary": "#F97316", "accent_a": "#EC4899", "accent_b": "#FACC15", "neutral": "#FFF7ED"},
    "S5": {"primary": "#7C2D12", "accent_a": "#FBBF24", "accent_b": "#FFFFFF", "neutral": "#1C1917"},
    "S6": {"primary": "#DC2626", "accent_a": "#16A34A", "accent_b": "#FACC15", "neutral": "#0A0A0A"},
}


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """按名称加载字体；缺失时回退到默认字体并打印警告。"""
    fp = ASSETS / "fonts" / name
    if fp.exists():
        return ImageFont.truetype(str(fp), size=size)
    print(f"[warn] font not found: {name}, fallback to default")
    return ImageFont.load_default()


def _gradient_mask(size, top=True, color=(0, 0, 0, 153)):
    """生成顶/底渐变遮罩，确保文字可读。"""
    w, h = size
    band_h = int(h * (0.45 if top else 0.35))
    band = Image.new("RGBA", (w, band_h), (0, 0, 0, 0))
    px = band.load()
    for y in range(band_h):
        alpha = int(color[3] * (1 - y / band_h)) if top else int(color[3] * (y / band_h))
        for x in range(w):
            px[x, y] = (color[0], color[1], color[2], alpha)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(band, (0, 0 if top else h - band_h), band)
    return canvas


def _paste_logo(canvas: Image.Image, scene_neutral: str):
    """放置 Logo —— 根据底色亮度选择亮版/暗版。"""
    # 简化：直接选 main 版本
    candidates = ["logo_gaming_main.png", "logo_gaming_light.png", "logo_gaming_dark.png"]
    logo_path = None
    for c in candidates:
        p = ASSETS / "logos" / c
        if p.exists():
            logo_path = p; break
    if not logo_path:
        print("[warn] logo not found, skip")
        return
    logo = Image.open(logo_path).convert("RGBA")
    # 占 Header 区高度的 40%，宽度按比例
    cw, ch = canvas.size
    target_h = int(ch * 0.35 * 0.40)
    ratio = target_h / logo.height
    logo = logo.resize((int(logo.width * ratio), target_h), Image.LANCZOS)
    # 落在左上安全区
    margin_x = int(cw * 0.08); margin_y = int(ch * 0.05)
    canvas.alpha_composite(logo, (margin_x, margin_y))


def _draw_title_block(canvas: Image.Image, brief: dict, palette: dict):
    cw, ch = canvas.size
    draw = ImageDraw.Draw(canvas)

    # 字号按 A3 基准 + 比例缩放
    base_h = 3508
    scale = ch / base_h

    title = brief.get("title", "")
    subtitle = brief.get("subtitle", "")

    f_title = _font("font_gaming_bold.ttf", int(200 * scale))
    f_sub = _font("font_gaming_bold.ttf", int(108 * scale))

    # 主标题落在 Hero 区上沿（约 35% 处）
    title_y = int(ch * 0.38)
    margin_x = int(cw * 0.08)

    # 标题阴影增强可读性
    shadow_offset = int(8 * scale)
    draw.text((margin_x + shadow_offset, title_y + shadow_offset), title,
              font=f_title, fill=(0, 0, 0, 180))
    draw.text((margin_x, title_y), title, font=f_title, fill="#FFFFFF")

    if subtitle:
        # 副标题色用 accent_a
        sub_y = title_y + int(220 * scale) + int(40 * scale)
        draw.text((margin_x, sub_y), subtitle, font=f_sub, fill=palette["accent_a"])


def _draw_info_block(canvas: Image.Image, brief: dict, palette: dict):
    cw, ch = canvas.size
    draw = ImageDraw.Draw(canvas)
    base_h = 3508
    scale = ch / base_h

    f_meta = _font("font_gaming_bold.ttf", int(40 * scale))
    margin_x = int(cw * 0.08)
    info_y = int(ch * 0.78)

    lines = []
    if brief.get("date"):     lines.append(f"日期 · {brief['date']}")
    if brief.get("location"): lines.append(f"地点 · {brief['location']}")
    if brief.get("host"):     lines.append(f"主办 · {brief['host']}")
    line_h = int(56 * scale)
    for i, line in enumerate(lines):
        # 阴影
        draw.text((margin_x + int(4 * scale), info_y + i * line_h + int(4 * scale)),
                  line, font=f_meta, fill=(0, 0, 0, 160))
        draw.text((margin_x, info_y + i * line_h), line, font=f_meta, fill="#FFFFFF")

    # Key points 标签条
    if brief.get("key_points"):
        f_kp = _font("font_gaming_bold.ttf", int(36 * scale))
        kp_y = int(ch * 0.62)
        for i, kp in enumerate(brief["key_points"][:4]):
            tag = f"  ▸ {kp}  "
            bbox = draw.textbbox((0, 0), tag, font=f_kp)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            pad = int(16 * scale)
            x = margin_x; y = kp_y + i * int(80 * scale)
            draw.rectangle([x, y, x + tw + pad * 2, y + th + pad * 2],
                           fill=palette["primary"])
            draw.text((x + pad, y + pad), tag, font=f_kp, fill="#FFFFFF")


def _paste_qr(canvas: Image.Image, qr_path: str | None):
    if not qr_path or not pathlib.Path(qr_path).exists():
        return
    cw, ch = canvas.size
    qr = Image.open(qr_path).convert("RGBA")
    target = int(ch * 0.12)
    qr = qr.resize((target, target), Image.LANCZOS)
    # 加白色外框防止融底
    frame = Image.new("RGBA", (target + 24, target + 24), (255, 255, 255, 255))
    frame.alpha_composite(qr, (12, 12))
    x = cw - frame.width - int(cw * 0.08)
    y = ch - frame.height - int(ch * 0.06)
    canvas.alpha_composite(frame, (x, y))


def compose(bg_path: str, brief: dict, out_path: str):
    canvas = Image.open(bg_path).convert("RGBA")
    palette = SCENE_PALETTE.get(brief.get("scene", "S1"), SCENE_PALETTE["S1"])

    # 顶/底渐变遮罩
    canvas.alpha_composite(_gradient_mask(canvas.size, top=True))
    canvas.alpha_composite(_gradient_mask(canvas.size, top=False))

    _paste_logo(canvas, palette["neutral"])
    _draw_title_block(canvas, brief, palette)
    _draw_info_block(canvas, brief, palette)
    _paste_qr(canvas, brief.get("qr_code"))

    pathlib.Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, format="PNG", optimize=True)
    # 同时输出 PDF（300dpi 友好）
    pdf_path = out_path.replace(".png", ".pdf")
    canvas.convert("RGB").save(pdf_path, format="PDF", resolution=300)
    return out_path, pdf_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bg", required=True)
    parser.add_argument("--brief", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    brief = json.loads(pathlib.Path(args.brief).read_text(encoding="utf-8"))
    out = args.out or f"output/{datetime.now().strftime('%Y%m%d_%H%M%S')}_final.png"
    png, pdf = compose(args.bg, brief, out)
    print(json.dumps({"png": png, "pdf": pdf}, ensure_ascii=False))


if __name__ == "__main__":
    main()
