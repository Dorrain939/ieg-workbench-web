"""
素材资源管理 —— logo、装饰图、纹理的加载与缓存。

约定：
- assets/logos/        —— 品牌 logo（含白色版、彩色版、emblem）
- assets/decorations/  —— 装饰素材（按 family 分类）
- assets/textures/     —— 可平铺的底纹（噪点、网格、点阵）
- assets/fonts/        —— 字体文件（display / body / mono）
"""
from __future__ import annotations
import pathlib
from typing import Optional, Dict
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"


# 在模块层缓存，重复使用同一张 logo 不重复 IO
_IMAGE_CACHE: Dict[str, Image.Image] = {}


def load_image(rel_path: str) -> Optional[Image.Image]:
    """从 assets/ 下加载一张图片，缓存且返回 RGBA。"""
    p = ASSETS / rel_path
    key = str(p)
    if key in _IMAGE_CACHE:
        return _IMAGE_CACHE[key].copy()
    if not p.exists():
        return None
    try:
        img = Image.open(p).convert("RGBA")
        _IMAGE_CACHE[key] = img
        return img.copy()
    except Exception as e:
        print(f"[warn] 加载素材失败: {p} -> {e}")
        return None


# ============================================================
# Logo 解析
# ============================================================
LOGO_SLOTS = {
    "horizontal": "logos/tencent-ieg-horizontal-white.png",
    "emblem":     "logos/tencent-ieg-emblem-white.png",
    "wordmark":   "logos/tencent-ieg-wordmark-white.png",
}


def get_logo(slot: str = "horizontal", target_height: Optional[int] = None) -> Optional[Image.Image]:
    """按槽位拿 logo。target_height 给定时按高度等比缩放。"""
    rel = LOGO_SLOTS.get(slot)
    if not rel:
        return None
    img = load_image(rel)
    if img is None:
        return None
    if target_height and img.height != target_height:
        ratio = target_height / img.height
        new_size = (int(img.width * ratio), target_height)
        img = img.resize(new_size, Image.LANCZOS)
    return img


def tint_logo(img: Image.Image, color: tuple) -> Image.Image:
    """把白色 logo 染成任意颜色（保持 alpha）。

    适合需要在浅底上展示时，把白 logo 染成品牌主色。
    color: (r, g, b)
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    r, g, b = color[:3]
    rgba = img.split()
    alpha = rgba[3]
    tinted = Image.new("RGBA", img.size, (r, g, b, 255))
    tinted.putalpha(alpha)
    return tinted
