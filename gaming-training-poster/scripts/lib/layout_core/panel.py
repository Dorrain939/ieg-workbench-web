def inset_box(box, pad: int):
    x0, y0, x1, y1 = box
    return x0 + pad, y0 + pad, x1 - pad, y1 - pad
