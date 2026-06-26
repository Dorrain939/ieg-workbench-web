"""Bridge new poster_strategy rules into legacy Python skills.

New project_type/scene/style rules are the source of truth. Legacy scene/tone
and palette fields are retained only as renderer compatibility values.
"""
from __future__ import annotations

from copy import deepcopy

PALETTE_BRIDGE = {
    "brand_blue_orange": "named:nebula_blue",
    "theme_by_keyword": "named:cyber_neon",
    "inherit_s5a_theme": "named:cyber_neon",
    "series_cyber_green": "named:engine_core",
    "inherit_s6a_series": "named:engine_core",
}


def _strategy(params: dict) -> dict:
    ps = params.get("project_strategy") or {}
    return ps if isinstance(ps, dict) else {}


def strategy_scene_id(params: dict, default: str = "S1") -> str:
    ps = _strategy(params)
    scene = ps.get("scene") or {}
    return scene.get("id") or params.get("scene") or default


def strategy_project_type(params: dict, default: str = "A") -> str:
    ps = _strategy(params)
    ptype = ps.get("project_type") or {}
    return ptype.get("id") or params.get("project_type") or default


def strategy_style_tokens(params: dict) -> dict:
    ps = _strategy(params)
    scene = ps.get("scene") or {}
    tokens = scene.get("style_tokens") or {}
    return tokens if isinstance(tokens, dict) else {}


def renderer_palette(params: dict, fallback: str = "named:cyber_neon") -> str:
    tokens = strategy_style_tokens(params)
    palette = tokens.get("palette") or params.get("palette_strategy") or ""
    return PALETTE_BRIDGE.get(palette, palette if str(palette).startswith("named:") else fallback)


STRUCTURED_RENDERERS = {
    "faculty_grid",
    "qa_block",
    "curriculum_timeline",
    "data_table",
    "complex_table",
    "cta_button",
    "contact_inline",
    "spec_text_panel",
    "spec_avatar_group_wall",
    "spec_course_card_list",
    "spec_feedback_story_flow",
    "spec_rating_bars",
    "spec_quote_cards",
    "spec_image_grid",
    "spec_image_text_split",
    "spec_action_bar",
}


def _module_renderer(module: dict) -> str:
    cap = module.get("capability") or {}
    return cap.get("renderer") or module.get("component") or ""


def _module_m_code(module: dict) -> int:
    key = str(module.get("script_key") or "")
    if not key.startswith("module.m"):
        return 0
    digits = []
    for ch in key[len("module.m"):]:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    try:
        return int("".join(digits)) if digits else 0
    except ValueError:
        return 0


def _module_kind(module: dict) -> str:
    key = str(module.get("script_key") or "")
    renderer = _module_renderer(module)
    m_code = _module_m_code(module)
    if m_code in {1, 2, 3, 14, 15} or renderer == "spec_text_panel":
        return "text_panel"
    if m_code == 4:
        return "plain_text"
    if m_code == 5:
        return "table"
    if m_code in {6, 8, 25}:
        return "image_text"
    if m_code in {7, 9}:
        return "feedback_flow"
    if m_code in {10, 16, 17, 18}:
        return "course_list"
    if m_code in {11, 12, 13}:
        return "faculty_lineup"
    if m_code == 19:
        return "rating_bars"
    if m_code in {20, 21}:
        return "image_grid"
    if m_code in {22, 23}:
        return "action_bar"
    if m_code == 24:
        return "contact_text"
    if key in {"module.faculty_grid", "module.guest_profile_deep"} or renderer in {"faculty_grid", "spec_avatar_group_wall"}:
        return "faculty_lineup"
    if renderer == "spec_course_card_list":
        return "course_list"
    if renderer == "spec_feedback_story_flow":
        return "feedback_flow"
    if renderer == "spec_rating_bars":
        return "rating_bars"
    if renderer == "spec_quote_cards":
        return "quote_cards"
    if renderer == "spec_image_grid":
        return "image_grid"
    if renderer == "spec_image_text_split":
        return "image_text"
    if renderer in {"spec_action_bar", "cta_button"} or key.endswith("_cta"):
        return "action_bar"
    if renderer == "qa_block":
        return "qa_block"
    if renderer == "curriculum_timeline":
        return "timeline"
    if renderer in {"data_table", "complex_table"} or key == "module.agenda_table":
        return "table"
    return ""


def _structured_section(module: dict) -> dict | None:
    cfg = module.get("module_config") or {}
    renderer = _module_renderer(module)
    kind = _module_kind(module)
    m_code = _module_m_code(module)
    if (renderer not in STRUCTURED_RENDERERS and not kind) or cfg.get("structured_enabled") is False:
        return None

    title = cfg.get("module_title") or module.get("name") or "模块"
    frame_mode = cfg.get("module_frame_mode") or ("upload" if cfg.get("module_frame_path") else "generated")
    if frame_mode not in {"generated", "upload", "none"}:
        frame_mode = "generated"
    asset_frame_path = cfg.get("module_frame_path") or ""
    if frame_mode != "upload":
        asset_frame_path = ""
    base = {
        "type": renderer,
        "title": cfg.get("inner_title") or "",
        "hide_title": True,
        "module_id": module.get("id"),
        "script_key": module.get("script_key"),
        "underline_color": cfg.get("underline_color") or "auto",
        "module_frame_mode": frame_mode,
        "panel_style": "none" if frame_mode == "none" else ("asset_frame" if frame_mode == "upload" and asset_frame_path else "generated"),
        "fill": None if cfg.get("panel_fill") in {None, "", "auto"} else cfg.get("panel_fill"),
        "outline": None if cfg.get("panel_border") in {None, "", "auto"} else cfg.get("panel_border"),
        "asset_frame_path": asset_frame_path,
        "asset_frame": asset_frame_path,
        "font_size": int(cfg.get("font_size") or 32),
        "font_family": cfg.get("font_family") or "default",
        "font_weight": cfg.get("font_weight") or "regular",
        "font_style": cfg.get("font_style") or "normal",
        "text_decoration": cfg.get("text_decoration") or "none",
        "text_align": cfg.get("text_align") or "left",
        "line_height": float(cfg.get("line_height") or 1.45),
        "paragraph_spacing": int(cfg.get("paragraph_spacing") or 18),
        "text_color": cfg.get("text_color") or "auto",
        "highlight_color": cfg.get("highlight_color") or "",
        "content_html": cfg.get("content_html") or "",
        "editor_json": cfg.get("editor_json") or cfg.get("content_editor_json") or None,
        "content_editor_json": cfg.get("content_editor_json") or cfg.get("editor_json") or None,
    }
    images = cfg.get("images") if isinstance(cfg.get("images"), list) else []

    if kind in {"text_panel", "plain_text", "contact_text"}:
        if kind == "contact_text":
            return {
                **base,
                "type": "contact_inline",
                "text": cfg.get("content") or "",
                "content_html": cfg.get("content_html") or "",
                "editor_json": cfg.get("editor_json") or cfg.get("content_editor_json") or None,
                "contacts": cfg.get("contacts") or [],
            }
        return {
            **base,
            "type": "spec_text_panel",
            "title": "",
            "text": cfg.get("content") or "",
            "subsections": cfg.get("subsections") or [],
            "list_items": cfg.get("list_items") or [],
            "images": images,
            "panel_style": "none" if kind == "plain_text" or frame_mode == "none" else base["panel_style"],
            "highlight_enabled": m_code == 2,
        }

    if kind == "faculty_lineup":
        mode = cfg.get("faculty_mode") or ("speaker_card" if module.get("script_key") == "module.guest_profile_deep" else "avatar_wall")
        speaker = cfg.get("speaker") or {}
        if mode in {"avatar_wall", "mixed"}:
            return {
                **base,
                "type": "spec_avatar_group_wall",
                "title": "",
                "faculty_mode": mode,
                "submodules": cfg.get("submodules") or [],
                "speaker": speaker if mode == "mixed" else {},
                "speaker_layout": cfg.get("layout") or "left_image_right_text",
            }
        speaker_sections = speaker.get("sections") or []
        text_parts = []
        for sec in speaker_sections:
            if not isinstance(sec, dict):
                continue
            heading = sec.get("title") or ""
            body = sec.get("text") or ""
            if heading or body:
                text_parts.append(f"{heading}\n{body}".strip())
        return {
            **base,
            "type": "spec_course_card_list",
            "title": "",
            "items": [{
                "title": speaker.get("name") or title,
                "text": "\n\n".join(text_parts) or cfg.get("content") or "",
                "image": speaker.get("avatar") or "",
                "layout": cfg.get("layout") or "left_image_right_text",
                "actions": speaker.get("actions") or [],
            }],
        }
    if kind == "speaker_card":
        speaker = cfg.get("speaker") or {}
        sections = speaker.get("sections") or []
        text_parts = []
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            heading = sec.get("title") or ""
            body = sec.get("text") or ""
            if heading or body:
                text_parts.append(f"{heading}\n{body}".strip())
        base["type"] = "spec_course_card_list"
        base["items"] = [{
            "title": speaker.get("name") or title,
            "text": "\n\n".join(text_parts) or cfg.get("content") or "",
            "image": speaker.get("avatar") or "",
            "layout": cfg.get("layout") or "left_image_right_text",
            "actions": speaker.get("actions") or [],
        }]
        return base
    if kind == "course_list":
        base["type"] = "spec_course_card_list"
        base["items"] = cfg.get("items") or cfg.get("submodules") or []
        return base
    if kind == "feedback_flow":
        base["type"] = "spec_feedback_story_flow"
        base["submodules"] = cfg.get("submodules") or []
        return base
    if kind == "rating_bars":
        base["type"] = "spec_rating_bars"
        base["items"] = cfg.get("items") or []
        return base
    if kind == "quote_cards":
        base["type"] = "spec_quote_cards"
        base["items"] = cfg.get("items") or []
        return base
    if kind == "image_grid":
        base["type"] = "spec_image_grid"
        base["images"] = images
        base["columns"] = cfg.get("columns") or (1 if m_code == 20 else 3)
        base["aspect_ratio"] = cfg.get("aspect_ratio") or 0.66
        return base
    if kind == "image_text":
        base["type"] = "spec_image_text_split"
        first_image = images[0].get("path") if images and isinstance(images[0], dict) else ""
        base.update({
            "layout": cfg.get("layout") or "left_image_right_text",
            "text": cfg.get("content") or "",
            "image": cfg.get("image") or first_image,
            "image_fit": "contain",
            "actions": cfg.get("actions") or [],
        })
        return base
    if kind == "action_bar":
        action = (cfg.get("actions") or [{}])[0] if isinstance(cfg.get("actions"), list) else {}
        base["type"] = "cta_button" if renderer == "cta_button" else "spec_action_bar"
        base.update(action or {})
        base["text"] = base.get("text") or cfg.get("content") or "立即报名"
        if action.get("hint"):
            base["hint"] = action.get("hint")
        return base
    if kind == "qa_block":
        base["type"] = "qa_block"
        base["items"] = cfg.get("items") or []
        return base
    if kind == "timeline":
        base["type"] = "curriculum_timeline"
        base["parts"] = cfg.get("parts") or []
        return base
    if kind == "table":
        table = {
            **base,
            "type": "data_table",
            "headers": cfg.get("headers") or [],
            "rows": cfg.get("rows") or [],
        }
        content = (cfg.get("content") or "").strip()
        if content:
            table["intro"] = content
        return table
    return None


def normalize_generation_params(params: dict) -> dict:
    params = deepcopy(params or {})
    ps = _strategy(params)
    if not ps:
        return params
    scene_id = strategy_scene_id(params)
    ptype = strategy_project_type(params)
    tokens = strategy_style_tokens(params)
    params["scene"] = scene_id
    params["project_type"] = ptype
    params["tone"] = "strategy_locked"
    params["style_strategy"] = (ps.get("project_type") or {}).get("style_strategy") or ""
    params["palette_strategy"] = tokens.get("palette") or ""
    params["legacy_renderer_palette"] = renderer_palette(params)
    params["module_execution_plan"] = [
        {
            "module_id": m.get("id"),
            "name": m.get("name"),
            "component": m.get("component"),
            "script_key": m.get("script_key"),
            "required": bool(m.get("required")),
            "status": m.get("status") or "script_pending",
        }
        for m in ps.get("module_plan", []) if isinstance(m, dict)
    ]
    return params


def apply_module_config_to_brief(brief: dict, params: dict) -> dict:
    """Apply editable strategy-module titles/colors/images to a rendered brief."""
    ps = _strategy(params)
    modules = [m for m in (ps.get("module_plan") or []) if isinstance(m, dict)]
    if not modules or not isinstance(brief, dict):
        return brief

    original_sections = list(brief.get("sections") or [])
    hero_sections = []
    for s in original_sections:
        if s.get("type") in {"hero_strip", "subtitle_text"}:
            hero_sections.append(s)
    if not hero_sections and original_sections:
        hero_sections = [original_sections[0]]
    editable_modules = [
        m for m in modules
        if (
            m.get("component") not in {"hero_strip", "series_identity", "top_logo_bar", "footer_logobar", "subtitle_text"}
            and m.get("script_key") not in {"module.series_identity", "module.series_identity_feedback"}
            and m.get("script_key") != "module.logo_endorsement"
        )
    ]

    rebuilt = list(hero_sections)
    for module in editable_modules:
        cfg = module.get("module_config") or {}
        title_enabled = cfg.get("title_enabled", True)
        if title_enabled:
            rebuilt.append({
                "type": "section_title_bar",
                "style": "plain",
                "text": cfg.get("module_title") or module.get("name") or "模块",
                "text_color": "#FFFFFF",
                "underline_color": cfg.get("underline_color") or "auto",
                "decoration_path": cfg.get("title_decoration_path") or "",
                "decoration_position": cfg.get("title_decoration_position") or "left",
                "decoration_size": int(cfg.get("title_decoration_size") or 42),
            })
        structured = _structured_section(module)
        if structured:
            if structured.get("type") == "module_group":
                rebuilt.extend(structured.get("sections") or [])
            else:
                rebuilt.append(structured)
            continue
        content = (cfg.get("content") or "").strip()
        if content:
            rebuilt.append({
                "type": "spec_text_panel",
                "title": "",
                "text": content,
                "content_html": cfg.get("content_html") or "",
                "editor_json": cfg.get("editor_json") or cfg.get("content_editor_json") or None,
                "content_editor_json": cfg.get("content_editor_json") or cfg.get("editor_json") or None,
                "module_id": module.get("id"),
                "script_key": module.get("script_key"),
                "module_frame_mode": cfg.get("module_frame_mode") or "generated",
                "panel_style": "none" if cfg.get("module_frame_mode") == "none" else ("asset_frame" if cfg.get("module_frame_mode") == "upload" and cfg.get("module_frame_path") else "generated"),
                "asset_frame_path": cfg.get("module_frame_path") if cfg.get("module_frame_mode") == "upload" else "",
                "fill": None if cfg.get("panel_fill") in {None, "", "auto"} else cfg.get("panel_fill"),
                "outline": None if cfg.get("panel_border") in {None, "", "auto"} else cfg.get("panel_border"),
                "images": cfg.get("images") or [],
                "font_size": int(cfg.get("font_size") or 32),
                "font_family": cfg.get("font_family") or "default",
                "font_weight": cfg.get("font_weight") or "regular",
                "font_style": cfg.get("font_style") or "normal",
                "text_decoration": cfg.get("text_decoration") or "none",
                "text_align": cfg.get("text_align") or "left",
                "line_height": float(cfg.get("line_height") or 1.45),
                "paragraph_spacing": int(cfg.get("paragraph_spacing") or 18),
                "text_color": cfg.get("text_color") or "auto",
                "highlight_color": cfg.get("highlight_color") or "",
            })
        for img in cfg.get("images") or []:
            if not isinstance(img, dict) or not img.get("path"):
                continue
            rebuilt.append({
                "type": "image_block",
                "image_path": img.get("path"),
                "caption": img.get("asset_label") or img.get("name") or "",
                "fit": "contain",
            })

    brief["sections"] = rebuilt
    title_cfg = (params.get("title_visual_config") or {}) if isinstance(params.get("title_visual_config"), dict) else {}
    logo_position = title_cfg.get("logo_position") or params.get("logo_position") or brief.get("logo_position") or "bottom"
    logo_paths = list(dict.fromkeys(brief.get("logos") or []))
    if logo_position != "none" and logo_paths:
        logo_section = {
            "type": "top_logo_bar",
            "_auto_logo_bar": True,
            "logos": logo_paths,
            "logo_height": int(title_cfg.get("logo_height") or params.get("logo_height") or brief.get("logo_height") or 76),
            "gap": int(title_cfg.get("logo_gap") or params.get("logo_gap") or brief.get("logo_gap") or 80),
            "align": title_cfg.get("logo_align") or params.get("logo_align") or brief.get("logo_align") or "center",
            "distribution": "even",
            "pad_top": 20,
            "pad_bottom": 20,
        }
        if logo_position == "top":
            rebuilt.insert(0, logo_section)
        else:
            rebuilt.append(logo_section)
    brief["_module_config_applied"] = True
    return brief
