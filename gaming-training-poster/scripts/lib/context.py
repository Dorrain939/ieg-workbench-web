"""共享渲染上下文。组件渲染时只读这个对象，不读全局变量。

v0.5 新增：
- occupied: 禁飞区列表（每个组件渲染完用 reserve() 把自己 bbox 注册进来），
  装饰 scatter 阶段会避开这些位置。
- bg_color_at(): 给定 (x,y) 估算底色，方便组件挑文字色（默认回退到 bg_colors[0]）。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Dict, Optional, List

from PIL import ImageFont, Image

from . import assets as A


@dataclass
class RenderContext:
    canvas_size: Tuple[int, int]
    margin_x: int
    palette: Dict[str, str]
    decoration_family: str
    font_path: Path
    font_path_display: Optional[Path] = None  # 标题字（可与 body 同一个）
    bg_base_color: str = "#0F0A2E"             # 兜底底色（给文字对比度选择用）
    canvas_cfg: Dict = field(default_factory=dict)  # v0.9.1：透传 brief.canvas，让组件知晓 AI 底图实际占用高度等
    _font_cache: Dict[str, ImageFont.FreeTypeFont] = field(default_factory=dict)
    occupied: List[Tuple[int, int, int, int]] = field(default_factory=list)  # (x0,y0,x1,y1)

    def font(self, size: int, role: str = "body") -> ImageFont.FreeTypeFont:
        """role: body | display | emphasis。

        v0.9.10：字体规则
        - display：W7（用于标题、CTA 按钮、艺术字、数字）
        - body：   W3（用于普通正文、说明、bullet 内容）
        - emphasis：W7 + 小一档（用于内嵌强调词，可选）

        说明：W3 在 1200 宽长海报上略偏细，建议正文绘制时配合 stroke_width=1
        做"伪粗"，由 components 自行 ImageDraw.text(..., stroke_width=1,
        stroke_fill=fill) 控制；本方法只负责选字体文件。
        """
        path = self.font_path_display if role in ("display", "emphasis") and self.font_path_display else self.font_path
        key = f"{role}:{size}:{path}"
        if key not in self._font_cache:
            try:
                self._font_cache[key] = ImageFont.truetype(str(path), size=size)
            except Exception:
                self._font_cache[key] = ImageFont.load_default()
        return self._font_cache[key]

    def body_text_kwargs(self, fill, base_kwargs=None) -> dict:
        """v0.9.10：W3 正文加粗助手。

        W3 在长海报上略细，调用方写：
            d.text((x,y), text, font=ctx.font(32,'body'),
                   **ctx.body_text_kwargs(fill='#1F2937'))
        实际效果 = ImageDraw.text(..., fill='#1F2937', stroke_width=1, stroke_fill='#1F2937')
        模拟轻度伪粗，避免 W3 在大海报上视觉发虚。
        """
        kw = dict(base_kwargs or {})
        kw.setdefault("fill", fill)
        kw.setdefault("stroke_width", 1)
        kw.setdefault("stroke_fill", fill)
        return kw

    @property
    def width(self) -> int:
        return self.canvas_size[0]

    @property
    def height(self) -> int:
        return self.canvas_size[1]

    @property
    def content_x0(self) -> int:
        return self.margin_x

    @property
    def content_x1(self) -> int:
        return self.canvas_size[0] - self.margin_x

    @property
    def content_w(self) -> int:
        return self.content_x1 - self.content_x0

    # ------- 素材便捷方法 -------
    def logo(self, slot: str = "horizontal", target_height: Optional[int] = None) -> Optional[Image.Image]:
        return A.get_logo(slot, target_height)

    # ------- v0.5 新增：禁飞区管理 -------
    def reserve(self, bbox: Tuple[int, int, int, int], pad: int = 16) -> None:
        """把刚渲染完的组件 bbox 注册到禁飞区，scatter 装饰时避让。pad: 外扩像素。"""
        x0, y0, x1, y1 = bbox
        self.occupied.append((x0 - pad, y0 - pad, x1 + pad, y1 + pad))

    def is_safe(self, bbox: Tuple[int, int, int, int]) -> bool:
        """判断 bbox 是否避开了所有禁飞区。"""
        x0, y0, x1, y1 = bbox
        for ox0, oy0, ox1, oy1 in self.occupied:
            if not (x1 <= ox0 or x0 >= ox1 or y1 <= oy0 or y0 >= oy1):
                return False
        return True
