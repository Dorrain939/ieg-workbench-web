def contain_size(width: int, height: int, max_width: int, max_height: int):
    scale = min(max_width / max(1, width), max_height / max(1, height))
    return int(width * scale), int(height * scale)
