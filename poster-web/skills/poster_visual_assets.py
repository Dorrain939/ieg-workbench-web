"""Apply gaming-training-poster §13 visual asset generation to poster briefs."""
from __future__ import annotations

import pathlib
import random
import re
from datetime import datetime
from typing import Callable

from image_client import ImageClient, ImageGenerationError


SCENE_LABEL = {"S1": "招生宣传", "S2": "开营通知", "S3": "课程预告", "S4": "结业总结", "S5": "晋升表彰", "S6": "电竞赛事"}
TONE_LABEL = {
    "auto": "AI 自动判断", "business": "专业稳重", "energetic": "活力激发",
    "warm": "温暖亲和", "tech": "科技前沿", "premium": "高端尊贵",
}


def _skill_root() -> pathlib.Path:
    web_root = pathlib.Path(__file__).resolve().parents[1]
    return web_root.parent / "gaming-training-poster"


def _safe_slug(text: str, fallback: str = "poster") -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:48] or fallback


def _find_hero(brief: dict) -> dict | None:
    for section in brief.get("sections") or []:
        if section.get("type") == "hero_strip":
            return section
    return None


def _find_title(brief: dict, project: dict) -> str:
    hero = _find_hero(brief) or {}
    card = hero.get("title_card") or {}
    lines = card.get("lines") or []
    if lines:
        return " ".join(str(x).strip() for x in lines if str(x).strip()) or project.get("name") or "培训海报"
    return project.get("name") or "培训海报"


def _find_subtitle(brief: dict) -> str:
    hero = _find_hero(brief) or {}
    card = hero.get("title_card") or {}
    return str(card.get("subtitle") or "").strip()


def _bg_colors(brief: dict) -> tuple[str, str]:
    colors = ((brief.get("canvas") or {}).get("bg_colors") or ["#1A0A3D", "#0D0520"])
    if len(colors) < 2:
        colors = [colors[0] if colors else "#1A0A3D", "#0D0520"]
    return str(colors[0]), str(colors[1])


def _context(project: dict, params: dict, brief: dict, title: str) -> str:
    scene = params.get("scene") or (brief.get("canvas") or {}).get("scene") or "S1"
    tone = params.get("tone") or "auto"
    extra = (params.get("extra") or "").strip()
    c1, c2 = _bg_colors(brief)
    return (
        f"项目名：{project.get('name') or title}\n"
        f"项目描述：{project.get('description') or '腾讯 IEG 内部培训海报'}\n"
        f"海报主标题：{title}\n"
        f"场景：{SCENE_LABEL.get(scene, scene)}\n"
        f"调性：{TONE_LABEL.get(tone, tone)}\n"
        f"主色参考：{c1} 到 {c2}\n"
        f"补充视觉要求：{extra or '无'}"
    )


def _relative_or_abs(path: pathlib.Path) -> str:
    return str(path)


def _clip_prompt(text: str, limit: int = 900) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit]


def _visual_assets(params: dict) -> list[dict]:
    assets = list(params.get("visual_assets") or [])
    title_cfg = params.get("title_visual_config") or {}
    if isinstance(title_cfg, dict):
        assets.extend(title_cfg.get("layer_assets") or [])
    if not isinstance(assets, list):
        return []
    deduped = []
    seen = set()
    for a in assets:
        if not isinstance(a, dict) or not a.get("path"):
            continue
        key = (a.get("asset_type") or "", a.get("path") or "")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(a)
    return deduped


def _first_asset(params: dict, *asset_types: str) -> dict | None:
    wanted = set(asset_types)
    for item in _visual_assets(params):
        if item.get("asset_type") in wanted:
            return item
    return None


def _assets_of(params: dict, *asset_types: str) -> list[dict]:
    wanted = set(asset_types)
    return [item for item in _visual_assets(params) if item.get("asset_type") in wanted]


def _apply_user_supplied_assets(brief: dict, params: dict, progress: Callable[[str], None]) -> dict:
    canvas = brief.setdefault("canvas", {})
    global_bg = _first_asset(params, "global_bg")
    hero_bg = _first_asset(params, "hero_bg")
    wordart = _first_asset(params, "main_wordart")
    subtitle_wordart = _first_asset(params, "subtitle_wordart")
    logos = _assets_of(params, "logo_color", "logo_black", "logo_white")
    decorations = _assets_of(params, "global_bg_decoration")

    if global_bg:
        canvas["global_bg_path"] = global_bg["path"]
        progress("已使用上传的全局底图")
    if hero_bg:
        canvas["bg_image_path"] = hero_bg["path"]
        progress("已使用上传的头部底图")
    if wordart:
        hero = _find_hero(brief)
        if not hero:
            title = brief.get("title") or "主标题"
            hero = {"type": "hero_strip", "height": 820, "title_card": {"lines": [title]}}
            brief.setdefault("sections", []).insert(0, hero)
        card = hero.setdefault("title_card", {})
        card["style"] = card.get("style") or "ai_wordart"
        card["image"] = wordart["path"]
        card.setdefault("chroma_key", False)
        progress("已使用上传的主标题艺术字")
    if subtitle_wordart:
        hero = _find_hero(brief)
        if hero:
            hero["subtitle_wordart_image"] = subtitle_wordart["path"]
            card = hero.setdefault("title_card", {})
            card["subtitle_wordart_image"] = subtitle_wordart["path"]
            card["subtitle"] = ""
            brief["sections"] = [s for s in (brief.get("sections") or []) if s.get("type") != "subtitle_text"]
            progress("已记录上传的副标题艺术字")
    if logos:
        brief["logos"] = [item["path"] for item in logos]
        progress(f"已使用上传的 Logo {len(logos)} 个")
    if decorations:
        bg = brief.setdefault("background_decorations", {"seed": 42, "exclude_top": 80, "exclude_bottom": 120, "types": []})
        types = bg.setdefault("types", [])
        for item in decorations:
            types.append({"path": item["path"], "size": [80, 180], "count": 8, "alpha": 0.45, "rotate": True, "blur": 0})
        progress(f"已加入上传的全局装饰元素 {len(decorations)} 个")
    return brief


def _apply_logo_bar_section(brief: dict, title_cfg: dict, params: dict) -> dict:
    logos = list(dict.fromkeys(brief.get("logos") or []))
    logo_position = title_cfg.get("logo_position") or params.get("logo_position") or brief.get("logo_position") or "bottom"
    sections = [s for s in (brief.get("sections") or []) if not s.get("_auto_logo_bar")]
    if logo_position == "none":
        brief["sections"] = sections
        return brief
    if not logos:
        brief["sections"] = sections
        return brief
    logo_section = {
        "type": "top_logo_bar",
        "_auto_logo_bar": True,
        "logos": logos,
        "logo_height": int(title_cfg.get("logo_height") or params.get("logo_height") or brief.get("logo_height") or 76),
        "gap": int(title_cfg.get("logo_gap") or params.get("logo_gap") or brief.get("logo_gap") or 80),
        "align": title_cfg.get("logo_align") or params.get("logo_align") or brief.get("logo_align") or "center",
        "distribution": "even",
        "pad_top": 20,
        "pad_bottom": 20,
    }
    if logo_position == "top":
        sections.insert(0, logo_section)
    else:
        sections.append(logo_section)
    brief["sections"] = sections
    return brief


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = str(hex_color or "#0D0520").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except Exception:
        return 13, 5, 32


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _write_geometric_global_bg(path: pathlib.Path, c1: str, c2: str, *, seed_text: str):
    """Stable L1 background: theme gradient plus low-density geometric decor."""
    from PIL import Image, ImageDraw, ImageFilter

    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1440, 2400
    rgb1, rgb2 = _hex_to_rgb(c1), _hex_to_rgb(c2)
    img = Image.new("RGB", (w, h), rgb2)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        # Smooth vertical gradient with subtle center glow.
        color = _blend(rgb1, rgb2, t)
        draw.line((0, y, w, y), fill=color)

    rng = random.Random(seed_text or "poster")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    accent_a = _blend(rgb1, (255, 255, 255), 0.42)
    accent_b = _blend(rgb2, (80, 220, 255), 0.35)
    accent_c = _blend(rgb1, (255, 190, 90), 0.22)

    # Large soft geometric ribbons, intentionally abstract and non-figurative.
    for _ in range(18):
        x = rng.randint(-260, w + 120)
        y = rng.randint(-120, h + 120)
        ww = rng.randint(220, 620)
        hh = rng.randint(80, 260)
        color = rng.choice([accent_a, accent_b, accent_c]) + (rng.randint(18, 42),)
        poly = [(x, y), (x + ww, y + rng.randint(-80, 80)), (x + ww - 90, y + hh), (x - 90, y + hh + rng.randint(-80, 80))]
        d.polygon(poly, fill=color)

    # Fine grid and particles: low density, leaves card space readable.
    for x in range(0, w, 96):
        d.line((x, 0, x, h), fill=(255, 255, 255, 10), width=1)
    for y in range(0, h, 120):
        d.line((0, y, w, y), fill=(255, 255, 255, 8), width=1)
    for _ in range(150):
        x, y = rng.randint(0, w), rng.randint(0, h)
        r = rng.randint(1, 4)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rng.randint(22, 60)))

    layer = layer.filter(ImageFilter.GaussianBlur(radius=1.2))
    out = img.convert("RGBA")
    out.alpha_composite(layer)
    out.convert("RGB").save(path)


def apply_gaming_visual_assets(brief: dict, project: dict, params: dict, progress: Callable[[str], None] | None = None) -> dict:
    """Generate or apply L1/L2/L3 assets and write them into brief per SKILL.md §13.

    User supplied visual_assets always win:
      global_bg -> canvas.global_bg_path
      hero_bg -> canvas.bg_image_path
      main_wordart -> hero_strip.title_card.image
      global_bg_decoration -> background_decorations.types[]
    Missing L1/L2/L3 assets are generated when generate_visual_assets is enabled.
    """
    progress = progress or (lambda _msg: None)
    canvas = brief.setdefault("canvas", {})
    canvas.setdefault("width", 1440)
    canvas.setdefault("bg_colors", ["#1A0A3D", "#0D0520"])

    title = _find_title(brief, project)
    subtitle = _find_subtitle(brief)
    scene = params.get("scene") or canvas.get("scene") or "S1"
    scene_slug = _safe_slug(f"{project.get('id') or project.get('name') or 'project'}-{scene}")
    title_slug = _safe_slug(title, "title")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    upload_dir = _skill_root() / "assets" / "uploads" / scene_slug
    c1, c2 = _bg_colors(brief)

    title_cfg = params.get("title_visual_config") or {}
    if not isinstance(title_cfg, dict):
        title_cfg = {}
    user_global_prompt = (title_cfg.get("global_bg_prompt") or params.get("global_bg_prompt") or "").strip()
    user_hero_prompt = (title_cfg.get("hero_bg_prompt") or params.get("hero_bg_prompt") or "").strip()
    user_wordart_prompt = (title_cfg.get("wordart_prompt") or params.get("wordart_prompt") or "").strip()
    user_subtitle = (title_cfg.get("subtitle_text") or params.get("subtitle_text") or "").strip()
    logo_position = title_cfg.get("logo_position") or params.get("logo_position") or "bottom"
    logo_align = title_cfg.get("logo_align") or params.get("logo_align") or "center"
    logo_height = int(title_cfg.get("logo_height") or params.get("logo_height") or 76)
    logo_gap = int(title_cfg.get("logo_gap") or params.get("logo_gap") or 80)
    brief["_visual_prompts"] = {
        "global_bg_prompt": user_global_prompt,
        "hero_bg_prompt": user_hero_prompt,
        "wordart_prompt": user_wordart_prompt,
    }

    brief = _apply_user_supplied_assets(brief, params, progress)
    if logo_position in {"top", "bottom", "none"}:
        brief["logo_position"] = logo_position
    brief["logo_align"] = logo_align
    brief["logo_height"] = logo_height
    brief["logo_gap"] = logo_gap
    brief = _apply_logo_bar_section(brief, title_cfg, params)
    canvas = brief.setdefault("canvas", {})
    hero = _find_hero(brief)
    card = (hero or {}).get("title_card") or {}

    missing_global = not bool(canvas.get("global_bg_path"))
    missing_hero = not bool(canvas.get("bg_image_path"))
    missing_wordart = not bool(card.get("image"))
    need_generation = missing_global or missing_hero or missing_wordart

    visual_mode = title_cfg.get("mode") or params.get("visual_strategy") or ""
    if params.get("generate_visual_assets") is False or visual_mode == "gradient_only":
        if need_generation:
            progress("已按配置跳过自动生图；仅使用已上传视觉素材和现有 brief 字段")
        return brief

    client = None
    if need_generation:
        client = ImageClient()
        if not client.is_configured:
            raise ImageGenerationError("生图模型未配置，无法执行 gaming-training-poster skill §13 的 L1/L2/L3 自动生图流程")

    upload_dir.mkdir(parents=True, exist_ok=True)

    if missing_global:
        global_path = upload_dir / f"global_bg_{title_slug}_{stamp}.png"
        if user_global_prompt:
            progress("正在按你的描述生成全局底图 L1（1440x2400）…")
            global_prompt = _clip_prompt(f"""
【必须优先执行的用户要求】{user_global_prompt}
生成一张腾讯 IEG 培训海报的 L1 全局底图，只做整张海报最底层背景。
画面必须是背景，不要主标题，不要正文，不要 logo，不要人物，不要角色，不要怪物，不要恐怖元素。
风格必须适合 HR/培训海报：干净、专业、现代、克制。
可以使用主题色纯色渐变、复杂几何装饰、抽象纹理、光线、粒子、网格，但要留出内容模块可读空间。
主题色参考：{c1}、{c2}。项目标题：{title}。
再次强调：严格按照用户要求生成全局底图：{user_global_prompt}
""")
            brief["_visual_prompts"]["global_bg_final_prompt"] = global_prompt
            client.generate(global_prompt, global_path, 1440, 2400, purpose="global_bg")
        else:
            progress("正在生成全局底图 L1（主题色渐变 + 几何装饰，1440x2400）…")
            _write_geometric_global_bg(global_path, c1, c2, seed_text=f"{title}-{scene}-{c1}-{c2}")
        canvas["global_bg_path"] = _relative_or_abs(global_path)

    if missing_hero:
        progress("正在按你的描述生成头部底图 L2（1440x800，主题抽象底图，中心留空，无人物无文字）…")
        hero_prompt = _clip_prompt(f"""
【必须优先执行的用户要求】{user_hero_prompt or '根据项目主题生成干净高级的头部底图，中心留空。'}
生成腾讯 IEG 培训海报的 L2 头部底图，只放在海报顶部，不是整张海报。
构图要求：中心区域必须留空，用来叠加主标题艺术字；装饰元素放在边缘和背景层。
风格要求：现代游戏行业培训视觉、抽象 UI 面板、几何结构、粒子、柔和光效、专业但有活力。
颜色必须贴合主题色：{c1}、{c2}，底部要能自然融入全局底图。
禁止：任何文字、字母、数字、logo、水印、人物、人脸、角色、怪物、武器、骷髅、恐怖、血腥、暴力。
项目标题：{title}。
再次强调：严格按照用户要求生成头部底图：{user_hero_prompt or '中心留空、抽象、专业、非恐怖。'}
""")
        brief["_visual_prompts"]["hero_bg_final_prompt"] = hero_prompt
        hero_path = upload_dir / f"hero_bg_{title_slug}_{stamp}.png"
        client.generate(hero_prompt, hero_path, 1440, 800, purpose="hero_bg")
        canvas["bg_image_path"] = _relative_or_abs(hero_path)

    if canvas.get("bg_image_path"):
        canvas["bg_image_fit"] = "width"
        canvas["bg_image_height"] = 800
        canvas["bg_image_bottom_fade_ratio"] = 0.30
        canvas["bg_image_chroma_key"] = False

    hero = _find_hero(brief)
    if hero is None:
        hero = {"type": "hero_strip", "height": 820, "title_card": {"lines": [title]}}
        brief.setdefault("sections", []).insert(0, hero)
    card = hero.setdefault("title_card", {})

    if not card.get("image"):
        progress("正在按你的描述生成主标题艺术字 L3（1440x400，纯黑底，渲染时自动抠黑）…")
        wordart_prompt = _clip_prompt(f"""
【必须优先执行的用户要求】{user_wordart_prompt or '现代游戏海报主标题艺术字，高级、清晰、可读。'}
生成腾讯 IEG 培训海报的 L3 主标题艺术字图片。
必须只绘制这个标题文字：{title}
背景必须是纯黑色 #000000，不透明，便于后续抠黑底。
文字要大、居中、清晰可读，有描边、立体感、内发光或主题色光效，专业但有游戏感。
禁止添加副标题、正文、logo、图标、吉祥物、人物、角色、怪物、恐怖元素、武器、骷髅、血腥、背景插画。
保留左右安全边距。
再次强调：严格按照用户要求生成艺术字：{user_wordart_prompt or '高级清晰的标题艺术字。'}
""")
        brief["_visual_prompts"]["wordart_final_prompt"] = wordart_prompt
        wordart_path = upload_dir / f"wordart_main_{title_slug}_{stamp}.png"
        client.generate(wordart_prompt, wordart_path, 1440, 400, purpose="wordart")
        card["image"] = _relative_or_abs(wordart_path)
        card["chroma_key"] = True
        card["chroma_bg_kind"] = "dark"
        card["key_lightness"] = 35
    else:
        card.setdefault("chroma_key", False)

    card["style"] = card.get("style") or "ai_wordart"
    card.setdefault("width_ratio", 0.86)
    card.setdefault("offset_from_bottom", 320)
    card["safe_zone"] = card.get("safe_zone") or "bottom"
    if title and not card.get("lines"):
        card["lines"] = [title]
    has_subtitle_wordart = bool(hero.get("subtitle_wordart_image") or card.get("subtitle_wordart_image"))
    if subtitle and not card.get("subtitle") and not has_subtitle_wordart:
        card["subtitle"] = subtitle
    if user_subtitle and not has_subtitle_wordart:
        card["subtitle"] = user_subtitle
        has_subtitle_section = any(s.get("type") == "subtitle_text" for s in brief.get("sections") or [])
        if not has_subtitle_section:
            insert_at = 1 if brief.get("sections") else 0
            brief.setdefault("sections", []).insert(insert_at, {
                "type": "subtitle_text",
                "text": user_subtitle,
                "font_size": 52,
                "frame_style": "none",
            })
    elif has_subtitle_wordart:
        brief["sections"] = [s for s in (brief.get("sections") or []) if s.get("type") != "subtitle_text"]
    hero["tight_bottom"] = True

    progress("已写入 brief：canvas.global_bg_path / canvas.bg_image_path / hero_strip.title_card.image")
    return brief
