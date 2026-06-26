def line_height(font_size: int, ratio: float = 1.45) -> int:
    return max(24, int(font_size * ratio))
