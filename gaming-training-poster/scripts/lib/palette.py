"""
色板 + 对比度工具：与 design-system.md 中的色 token 同步。
"""
from __future__ import annotations
from typing import Tuple

# 与 references/design-system.md 一致；用户提供品牌色后在此处覆盖
SCENE_PALETTE: dict[str, dict[str, str]] = {
    "S1": {"primary": "#3B82F6", "accent_a": "#FBBF24", "accent_b": "#10B981", "neutral": "#0F172A"},
    "S2": {"primary": "#1E1B4B", "accent_a": "#C9A961", "accent_b": "#475569", "neutral": "#0B1020"},
    "S3": {"primary": "#0F172A", "accent_a": "#22D3EE", "accent_b": "#A78BFA", "neutral": "#020617"},
    "S4": {"primary": "#F97316", "accent_a": "#EC4899", "accent_b": "#FACC15", "neutral": "#FFF7ED"},
    "S5": {"primary": "#7C2D12", "accent_a": "#FBBF24", "accent_b": "#FFFFFF", "neutral": "#1C1917"},
    "S6": {"primary": "#DC2626", "accent_a": "#16A34A", "accent_b": "#FACC15", "neutral": "#0A0A0A"},
}


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


def luminance(rgb: Tuple[int, int, int]) -> float:
    def lin(c: float) -> float:
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> float:
    la, lb = luminance(a), luminance(b)
    L1, L2 = max(la, lb), min(la, lb)
    return (L1 + 0.05) / (L2 + 0.05)


def pick_text_color_on(bg: Tuple[int, int, int]) -> str:
    """根据背景亮度选择白/黑字。"""
    return "#FFFFFF" if luminance(bg) < 0.45 else "#0E0F1A"


def get_palette(scene_id: str) -> dict[str, str]:
    return SCENE_PALETTE.get(scene_id, SCENE_PALETTE["S1"])
