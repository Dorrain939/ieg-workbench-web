"""
质量自检：交付前最后一道关。
任何一项失败 → 返回 issue 列表，由 SKILL.md 流程决定是否重抽。
"""
from __future__ import annotations
import json, pathlib, argparse
from PIL import Image


def _luminance(rgb):
    r, g, b = [c / 255.0 for c in rgb[:3]]
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    L1, L2 = max(la, lb), min(la, lb)
    return (L1 + 0.05) / (L2 + 0.05)


def check_text_contrast(img_path: str) -> dict:
    """简化检查：抽样顶部/底部条带的平均色，与白字对比度应 ≥ 4.5。"""
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    top_band = img.crop((0, 0, w, int(h * 0.35))).resize((1, 1)).getpixel((0, 0))
    bot_band = img.crop((0, int(h * 0.75), w, h)).resize((1, 1)).getpixel((0, 0))
    white = (255, 255, 255)
    return {
        "top_contrast": round(_contrast(top_band, white), 2),
        "bottom_contrast": round(_contrast(bot_band, white), 2),
        "pass_top": _contrast(top_band, white) >= 4.5,
        "pass_bottom": _contrast(bot_band, white) >= 4.5,
    }


def check_filesize(img_path: str, max_mb: float = 5.0) -> dict:
    size_mb = pathlib.Path(img_path).stat().st_size / 1024 / 1024
    return {"size_mb": round(size_mb, 2), "pass": size_mb <= max_mb}


def check_dimensions(img_path: str) -> dict:
    img = Image.open(img_path)
    return {"width": img.width, "height": img.height,
            "pass": img.width >= 1024 and img.height >= 1024}


def run(img_path: str) -> dict:
    report = {
        "contrast": check_text_contrast(img_path),
        "filesize": check_filesize(img_path),
        "dimensions": check_dimensions(img_path),
    }
    issues = []
    if not report["contrast"]["pass_top"]:
        issues.append("顶部文字区对比度不足，需要更深的渐变遮罩或更亮的文字色")
    if not report["contrast"]["pass_bottom"]:
        issues.append("底部信息区对比度不足，需要更深的渐变遮罩")
    if not report["filesize"]["pass"]:
        issues.append("文件超过 5MB，需要压缩")
    if not report["dimensions"]["pass"]:
        issues.append("尺寸不足以印刷")
    report["issues"] = issues
    report["pass"] = len(issues) == 0
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    args = ap.parse_args()
    r = run(args.img)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
