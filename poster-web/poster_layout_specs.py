"""Poster layout spec registry.

The system should choose a visual specification first, then fill it with
content. These specs are rendered by Python functions in the long-poster engine.
"""
from __future__ import annotations


LAYOUT_SPECS = [
    {
        "spec_id": "text_panel",
        "category": "text",
        "label": "纯文字框",
        "renderer": "spec_text_panel",
        "supports_submodules": False,
        "supports_actions": False,
        "fields": ["title", "text", "bullets"],
    },
    {
        "spec_id": "image_grid",
        "category": "image",
        "label": "纯图片网格",
        "renderer": "spec_image_grid",
        "supports_submodules": False,
        "supports_actions": False,
        "fields": ["title", "images", "columns", "aspect_ratio"],
    },
    {
        "spec_id": "image_text_split",
        "category": "image_text",
        "label": "普通图文混排",
        "renderer": "spec_image_text_split",
        "supports_submodules": False,
        "supports_actions": True,
        "layout_forms": ["left_image_right_text", "right_image_left_text", "top_image_bottom_text", "bottom_image_top_text"],
        "fields": ["title", "image", "text", "layout", "actions"],
    },
    {
        "spec_id": "avatar_group_wall",
        "category": "people",
        "label": "分组圆头像墙",
        "renderer": "spec_avatar_group_wall",
        "supports_submodules": True,
        "supports_actions": False,
        "submodule_schema": {"title": "string", "columns": "number", "items": ["avatar", "name", "org"]},
    },
    {
        "spec_id": "rating_bars",
        "category": "metric",
        "label": "横向评分条",
        "renderer": "spec_rating_bars",
        "supports_submodules": False,
        "supports_actions": False,
        "fields": ["title", "items[label,score,max]"],
    },
    {
        "spec_id": "action_bar",
        "category": "action",
        "label": "独立 CTA 按钮",
        "renderer": "spec_action_bar",
        "supports_submodules": False,
        "supports_actions": False,
        "fields": ["text", "placement", "style", "link", "qr_image"],
    },
    {
        "spec_id": "quote_cards",
        "category": "feedback",
        "label": "反馈引言卡片组",
        "renderer": "spec_quote_cards",
        "supports_submodules": False,
        "supports_actions": False,
        "fields": ["title", "items[text,author]", "columns"],
    },
    {
        "spec_id": "course_card_list",
        "category": "course",
        "label": "课程/讲师介绍大模块",
        "renderer": "spec_course_card_list",
        "supports_submodules": True,
        "supports_actions": True,
        "submodule_schema": {"title": "string", "layout": "image_text_split", "image": "path", "text": "string", "actions": "array"},
    },
    {
        "spec_id": "feedback_story_flow",
        "category": "feedback",
        "label": "反馈故事流",
        "renderer": "spec_feedback_story_flow",
        "supports_submodules": True,
        "supports_actions": True,
        "submodule_schema": {"layout_form": "rating_bars|image_text_split|image_grid", "fields": "layout-specific"},
    },
]


SPEC_MAP = {item["spec_id"]: item for item in LAYOUT_SPECS}


LEGACY_MODULE_SPEC_MAP = {
    "module.project_background": "text_panel",
    "module.training_goals": "text_panel",
    "module.project_content": "text_panel",
    "module.project_timeline": "image_text_split",
    "module.faculty_grid": "avatar_group_wall",
    "module.guest_profile_deep": "course_card_list",
    "module.agenda_table": "text_panel",
    "module.course_rating": "rating_bars",
    "module.rating_summary": "rating_bars",
    "module.event_multidim_rating": "rating_bars",
    "module.student_voice": "quote_cards",
    "module.feedback_gain_suggestion": "quote_cards",
    "module.photo_collage": "image_grid",
    "module.group_photo": "image_grid",
    "module.work_showcase": "image_grid",
    "module.course_matrix": "course_card_list",
    "module.course_card": "course_card_list",
    "module.course_feedback_card": "feedback_story_flow",
    "module.course_feedback_schema": "feedback_story_flow",
}


def list_layout_specs() -> dict:
    return {
        "version": "poster_layout_specs.v1",
        "specs": LAYOUT_SPECS,
        "legacy_module_spec_map": LEGACY_MODULE_SPEC_MAP,
    }


def resolve_spec(spec_id: str) -> dict | None:
    return SPEC_MAP.get(spec_id)
