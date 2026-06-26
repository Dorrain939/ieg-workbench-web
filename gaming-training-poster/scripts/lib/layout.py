"""
栅格 / 排版引擎：把 design-system.md 的规则编译成可调用的坐标。
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h


@dataclass
class PosterLayout:
    canvas_w: int
    canvas_h: int
    margin_ratio: float = 0.08

    @property
    def header(self) -> Rect:
        m = int(self.canvas_w * self.margin_ratio)
        return Rect(m, int(self.canvas_h * 0.05),
                   self.canvas_w - 2 * m, int(self.canvas_h * 0.30))

    @property
    def hero(self) -> Rect:
        m = int(self.canvas_w * self.margin_ratio)
        return Rect(m, int(self.canvas_h * 0.35),
                   self.canvas_w - 2 * m, int(self.canvas_h * 0.40))

    @property
    def info(self) -> Rect:
        m = int(self.canvas_w * self.margin_ratio)
        return Rect(m, int(self.canvas_h * 0.75),
                   self.canvas_w - 2 * m, int(self.canvas_h * 0.20))

    def scale(self) -> float:
        """以 A3 高度为基准的字号缩放系数。"""
        return self.canvas_h / 3508


SIZE_PRESETS = {
    "A3":      (1024, 1536),    # 2:3
    "A4":      (1024, 1448),
    "公众号头图": (1280, 720),
    "朋友圈":   (1080, 1080),
}


def get_layout(size_name: str = "A3") -> PosterLayout:
    w, h = SIZE_PRESETS.get(size_name, SIZE_PRESETS["A3"])
    return PosterLayout(canvas_w=w, canvas_h=h)
