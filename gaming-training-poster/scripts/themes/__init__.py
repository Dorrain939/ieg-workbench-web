"""主题包注册表。

主题包不影响默认行为：用户 brief 不写 theme 字段，就跟以前完全一样。
写了 theme 字段的，会在 compose_long_poster 入口处把主题默认值合并进 brief。
"""
from .ai_bootcamp import get_theme as _get_ai_bootcamp, apply_theme_to_brief

__all__ = ["apply_theme_to_brief"]
