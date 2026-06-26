"""Module capability registry for the new poster strategy.

The strategy plan says what a poster should contain. This registry says whether
each planned module is backed by an existing Python renderer/script today.
"""
from __future__ import annotations

from copy import deepcopy


STATUS_READY = "ready"
STATUS_NEEDS_ENHANCEMENT = "needs_enhancement"
STATUS_MISSING = "missing"


STATUS_LABELS = {
    STATUS_READY: "可直接复用",
    STATUS_NEEDS_ENHANCEMENT: "可复用但需增强",
    STATUS_MISSING: "缺脚本/需新开发",
}

MODULE_LABELS = {
    "module.hero_title": "标题区视觉层",
    "module.theme_hero": "主题标题区",
    "module.theme_hero_review": "回顾标题区",
    "module.series_identity": "系列识别标题区",
    "module.series_identity_feedback": "系列反馈标题区",
    "module.project_background": "项目背景",
    "module.project_overview": "项目概览",
    "module.project_content": "项目内容",
    "module.project_recap": "项目回顾",
    "module.completion_response": "结项回应",
    "module.closing_blessing": "收尾祝福",
    "module.training_goals": "培养目标",
    "module.share_outline": "分享提纲",
    "module.share_recap": "分享回顾",
    "module.event_summary": "活动摘要",
    "module.signup_notice": "报名须知",
    "module.core_question": "核心问题",
    "module.next_preview": "下期预告",
    "module.series_next": "系列导航/下期入口",
    "module.faculty_grid": "讲师/嘉宾头像墙",
    "module.guest_profile_deep": "嘉宾深度介绍",
    "module.agenda_table": "日程/安排表",
    "module.logo_endorsement": "品牌 Logo 视觉层",
    "module.signup_cta": "报名按钮",
    "module.replay_cta": "回放按钮",
    "module.qa_interview": "访谈问答",
    "module.project_timeline": "项目时间轴",
    "module.full_timeline": "完整历程时间轴",
    "module.photo_collage": "活动照片墙",
    "module.group_photo": "大合影展示",
    "module.course_matrix": "课程矩阵",
    "module.course_rating": "课程评分",
    "module.rating_summary": "评分汇总",
    "module.event_multidim_rating": "多维评分",
    "module.student_voice": "学员反馈",
    "module.feedback_gain_suggestion": "收获与建议反馈",
    "module.work_showcase": "作品/成果展示",
    "module.mentor_quote": "导师寄语",
    "module.course_card": "课程卡片",
    "module.course_feedback_card": "课程反馈卡片",
    "module.course_feedback_schema": "课程反馈子结构",
}

MODULE_LABELS.update({
    "module.tm1_tm13_visual_layer": "TM1-TM13 标题区视觉层",
    "module.tm1_top_logo": "TM1 顶部 Logo",
    "module.tm2_bottom_logo": "TM2 底部 Logo",
    "module.tm3_global_bg": "TM3 全局底图",
    "module.tm4_hero_bg": "TM4 头部底图",
    "module.tm5_main_wordart": "TM5 主标题艺术字",
    "module.tm6_subtitle_wordart": "TM6 副标题艺术字",
    "module.tm7_main_title_decoration": "TM7 主标题装饰图",
    "module.tm8_subtitle_decoration": "TM8 副标题装饰图",
    "module.tm9_section_title_plain": "TM9 模块标题（简洁下划线）",
    "module.tm10_section_title_left_card": "TM10 模块标题（左侧标题卡）",
    "module.tm11_section_title_center_card": "TM11 模块标题（居中标题卡）",
    "module.tm12_section_title_decoration": "TM12 模块标题装饰图",
    "module.tm13_module_frame": "TM13 模块底框/背景素材",
    "module.m1_text": "M1 纯文字",
    "module.m2_highlight_text": "M2 纯文字（含高亮）",
    "module.m3_text_subsections": "M3 纯文字父子模块",
    "module.m4_plain_text": "M4 无底框纯文字",
    "module.m5_text_table": "M5 文字 + 表格",
    "module.m6_image_text_single": "M6 单图图文",
    "module.m7_image_text_subsections": "M7 图文父子模块",
    "module.m8_single_image_text": "M8 文字 + 单图",
    "module.m9_multi_image_text": "M9 文字 + 多图",
    "module.m10_single_person_card": "M10 单人卡片",
    "module.m11_person_cards_row": "M11 多张单人头像卡片",
    "module.m12_avatar_wall": "M12 多人头像墙",
    "module.m13_avatar_wall_groups": "M13 多人头像墙父子模块",
    "module.m14_text_name_list": "M14 纯文字名单",
    "module.m15_text_name_list_groups": "M15 纯文字名单父子模块",
    "module.m16_course_speaker_split": "M16 课程卡片（左讲师右课程）",
    "module.m17_course_text_speaker": "M17 课程卡片（上文下讲师）",
    "module.m18_course_parent_children": "M18 多课程父子模块",
    "module.m19_rating_bars": "M19 课程评分条",
    "module.m20_single_image": "M20 纯图片单张",
    "module.m21_multi_image_collage": "M21 纯图片拼盘",
    "module.m22_button_inside": "M22 按钮（模块内）",
    "module.m23_button_outside": "M23 按钮（模块外）",
    "module.m24_contact_text": "M24 联系方式文字",
    "module.m25_contact_qr": "M25 联系方式二维码",
})


RENDERER_CAPABILITIES = {
    "hero_strip": {
        "renderer": "hero_strip",
        "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip",
        "status": STATUS_READY,
        "notes": "支持头部底图、标题卡、AI 艺术字图；需由视觉素材流程写入 L1/L2/L3。",
    },
    "lead_paragraph": {
        "renderer": "lead_paragraph",
        "python": "gaming-training-poster/scripts/lib/components.py::render_lead_paragraph",
        "status": STATUS_READY,
        "notes": "适合项目背景、回顾正文、祝福语等普通正文块。",
    },
    "bullet_points_block": {
        "renderer": "bullet_points_block",
        "python": "gaming-training-poster/scripts/lib/components.py::render_bullet_points_block",
        "status": STATUS_READY,
        "notes": "适合培养目标、分享提纲、收获列表。",
    },
    "info_card": {
        "renderer": "info_card",
        "python": "gaming-training-poster/scripts/lib/components.py::render_info_card",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有信息卡渲染；活动摘要、项目内容等需要补稳定字段 schema。",
    },
    "notice_box": {
        "renderer": "notice_box",
        "python": "gaming-training-poster/scripts/lib/components.py::render_notice_box",
        "status": STATUS_READY,
        "notes": "适合温馨提示、核心问题、下期预告、系列导航。",
    },
    "faculty_grid": {
        "renderer": "faculty_grid",
        "python": "gaming-training-poster/scripts/lib/components.py::render_faculty_grid",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有讲师/嘉宾网格；头像、姓名、职称、长简介匹配需要增强。",
    },
    "data_table": {
        "renderer": "data_table",
        "python": "gaming-training-poster/scripts/lib/components.py::render_data_table",
        "status": STATUS_READY,
        "notes": "适合普通二维表格、日程、安排。",
    },
    "complex_table": {
        "renderer": "complex_table",
        "python": "gaming-training-poster/scripts/lib/components.py::render_complex_table",
        "status": STATUS_READY,
        "notes": "支持复杂表格的合并单元格数据结构。",
    },
    "table_module": {
        "renderer": "table_module",
        "python": "gaming-training-poster/scripts/lib/poster_table_module.py",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有 Word/Excel/复杂表格转图片能力；要接入新策略的课程矩阵 schema。",
    },
    "top_logo_bar": {
        "renderer": "top_logo_bar",
        "python": "gaming-training-poster/scripts/lib/components.py::render_top_logo_bar",
        "status": STATUS_READY,
        "notes": "适合底部品牌背书和 Logo 条。",
    },
    "cta_button": {
        "renderer": "cta_button",
        "python": "gaming-training-poster/scripts/lib/components.py::render_cta_button",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "单 CTA 可复用；系列课程的每课独立报名要新增 course_cards 包装。",
    },
    "qa_block": {
        "renderer": "qa_block",
        "python": "gaming-training-poster/scripts/lib/components.py::render_qa_block",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有 Q&A 基础块；策略中的 qa_card 需要映射和访谈样式。",
    },
    "curriculum_timeline": {
        "renderer": "curriculum_timeline",
        "python": "gaming-training-poster/scripts/lib/components.py::render_curriculum_timeline",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有课程时间轴；项目周期和完整回顾历程需要新模式。",
    },
    "image_block": {
        "renderer": "image_block",
        "python": "gaming-training-poster/scripts/lib/components.py::render_image_block",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有单图插入；照片墙、大合影、作品展示需要专用布局。",
    },
}


MODULE_CAPABILITIES = {
    "module.hero_title": {"base": "hero_strip"},
    "module.theme_hero": {"base": "hero_strip"},
    "module.theme_hero_review": {"base": "hero_strip"},
    "module.project_background": {"base": "lead_paragraph"},
    "module.completion_response": {"base": "lead_paragraph"},
    "module.project_overview": {"base": "lead_paragraph"},
    "module.share_recap": {"base": "lead_paragraph"},
    "module.series_intro": {"base": "lead_paragraph"},
    "module.closing_blessing": {"base": "lead_paragraph"},
    "module.training_goals": {"base": "bullet_points_block"},
    "module.share_outline": {"base": "bullet_points_block"},
    "module.project_content": {"base": "info_card"},
    "module.project_recap": {"base": "info_card"},
    "module.event_summary": {"base": "info_card"},
    "module.signup_notice": {"base": "notice_box"},
    "module.core_question": {"base": "notice_box"},
    "module.next_preview": {"base": "notice_box"},
    "module.series_next": {"base": "notice_box"},
    "module.faculty_grid": {"base": "faculty_grid"},
    "module.guest_profile_deep": {
        "renderer": "spec_course_card_list",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "单个讲师深度卡：头像/照片 + 头衔 + 经历背景/研究方向/课程亮点等分段介绍。",
    },
    "module.agenda_table": {"base": "data_table"},
    "module.logo_endorsement": {"base": "top_logo_bar"},
    "module.signup_cta": {"base": "cta_button"},
    "module.replay_cta": {"base": "cta_button"},
    "module.qa_interview": {
        "base": "qa_block",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "策略组件名是 qa_card；当前需桥接到 qa_block，并补访谈卡片样式。",
    },
    "module.project_timeline": {
        "base": "curriculum_timeline",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "可借课程时间轴，但要补项目周期字段和节奏样式。",
    },
    "module.full_timeline": {
        "base": "curriculum_timeline",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "可扩展时间轴；需要支持多轮集中、结项答辩、成果节点。",
    },
    "module.photo_collage": {
        "renderer": "spec_image_grid",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_grid",
        "status": STATUS_READY,
        "notes": "已新增规格化图片网格，支持多图裁切、安全留白和标题容器。",
    },
    "module.group_photo": {
        "renderer": "spec_image_grid",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_grid",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "可用图片规格承接；大合影还需要更精细的人脸安全裁切。",
    },
    "module.course_matrix": {
        "renderer": "spec_course_card_list",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已新增课程卡片列表规格；课程矩阵表格化仍需 schema 增强。",
    },
    "module.course_rating": {
        "renderer": "spec_rating_bars",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_rating_bars",
        "status": STATUS_READY,
        "notes": "已新增横向评分条规格。",
    },
    "module.rating_summary": {
        "renderer": "spec_rating_bars",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_rating_bars",
        "status": STATUS_READY,
        "notes": "已新增评分条规格，可承接全项目评分汇总。",
    },
    "module.event_multidim_rating": {
        "renderer": "spec_rating_bars",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_rating_bars",
        "status": STATUS_READY,
        "notes": "已新增多项评分条规格。",
    },
    "module.student_voice": {
        "renderer": "spec_quote_cards",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_quote_cards",
        "status": STATUS_READY,
        "notes": "已新增反馈引言卡片组规格。",
    },
    "module.feedback_gain_suggestion": {
        "renderer": "spec_quote_cards",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_quote_cards",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "可用反馈卡片组承接；分类双栏样式后续增强。",
    },
    "module.work_showcase": {
        "renderer": "spec_image_grid",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_grid",
        "status": STATUS_READY,
        "notes": "已新增图片展示规格，可承接作品和成果展示。",
    },
    "module.mentor_quote": {
        "renderer": "spec_quote_cards",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_quote_cards",
        "status": STATUS_READY,
        "notes": "已新增引言卡片规格，可承接导师寄语。",
    },
    "module.series_identity": {
        "renderer": "hero_strip",
        "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip",
        "status": STATUS_READY,
        "notes": "系列识别并入标题区视觉层，复用全局底图、头部底图、主标题艺术字、副标题、Logo 位置等能力。",
    },
    "module.series_identity_feedback": {
        "renderer": "hero_strip",
        "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip",
        "status": STATUS_READY,
        "notes": "系列反馈识别并入标题区视觉层，反馈场景由标题、副标题、头图和风格参数区分。",
    },
    "module.course_card": {
        "renderer": "spec_course_card_list",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list",
        "status": STATUS_READY,
        "notes": "已新增课程卡片列表规格，支持每个子课程内 actions。",
    },
    "module.course_feedback_card": {
        "renderer": "spec_feedback_story_flow",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_feedback_story_flow",
        "status": STATUS_READY,
        "notes": "已新增反馈故事流规格。",
    },
    "module.course_feedback_schema": {
        "renderer": "spec_feedback_story_flow",
        "python": "gaming-training-poster/scripts/lib/components.py::render_spec_feedback_story_flow",
        "status": STATUS_NEEDS_ENHANCEMENT,
        "notes": "已有故事流渲染底座；讲师/评分/三分反馈 schema 仍需解析增强。",
    },
}

MODULE_CAPABILITIES.update({
    "module.tm1_tm13_visual_layer": {"renderer": "hero_strip", "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip", "status": STATUS_READY, "notes": "TM1-TM13：标题区与全局视觉资产集合，包含 Logo、全局底图、头部底图、主副标题艺术字、标题装饰和模块素材框。"},
    "module.tm1_top_logo": {"renderer": "top_logo_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_top_logo_bar", "status": STATUS_READY, "notes": "TM1：顶部 Logo，支持均匀排列、大小和间距配置。"},
    "module.tm2_bottom_logo": {"renderer": "top_logo_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_top_logo_bar", "status": STATUS_READY, "notes": "TM2：底部 Logo，支持均匀排列、大小和间距配置。"},
    "module.tm3_global_bg": {"renderer": "global_background", "python": "gaming-training-poster/scripts/lib/bg_decor.py", "status": STATUS_READY, "notes": "TM3：全局底图，支持上传或生图模型生成。"},
    "module.tm4_hero_bg": {"renderer": "hero_strip", "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip", "status": STATUS_READY, "notes": "TM4：头部底图，放在标题区顶部主视觉位置。"},
    "module.tm5_main_wordart": {"renderer": "hero_strip", "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip", "status": STATUS_READY, "notes": "TM5：主标题艺术字图，支持上传或生图模型生成。"},
    "module.tm6_subtitle_wordart": {"renderer": "subtitle_text", "python": "gaming-training-poster/scripts/lib/components.py::render_subtitle_text", "status": STATUS_READY, "notes": "TM6：副标题艺术字或副标题文字图层。"},
    "module.tm7_main_title_decoration": {"renderer": "hero_strip", "python": "gaming-training-poster/scripts/lib/components.py::render_hero_strip", "status": STATUS_READY, "notes": "TM7：主标题装饰素材。"},
    "module.tm8_subtitle_decoration": {"renderer": "subtitle_text", "python": "gaming-training-poster/scripts/lib/components.py::render_subtitle_text", "status": STATUS_READY, "notes": "TM8：副标题装饰素材。"},
    "module.tm9_section_title_plain": {"renderer": "section_title_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_section_title_bar", "status": STATUS_READY, "notes": "TM9：居中简洁白字标题 + 可配置下划线。"},
    "module.tm10_section_title_left_card": {"renderer": "section_title_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_section_title_bar", "status": STATUS_NEEDS_ENHANCEMENT, "notes": "TM10：左侧标题卡样式，复用 section_title_bar 并预留素材卡增强。"},
    "module.tm11_section_title_center_card": {"renderer": "section_title_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_section_title_bar", "status": STATUS_NEEDS_ENHANCEMENT, "notes": "TM11：居中标题卡样式，复用 section_title_bar 并预留素材卡增强。"},
    "module.tm12_section_title_decoration": {"renderer": "section_title_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_section_title_bar", "status": STATUS_READY, "notes": "TM12：模块标题左右装饰小素材。"},
    "module.tm13_module_frame": {"renderer": "asset_frame", "python": "gaming-training-poster/scripts/lib/components.py::_draw_asset_frame", "status": STATUS_READY, "notes": "TM13：模块底框/背景素材，作为普通内容模块的底层框。"},
    "module.m1_text": {"renderer": "spec_text_panel", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_text_panel", "status": STATUS_READY, "notes": "M1：普通纯文字框，适合项目背景、简介、致谢。"},
    "module.m2_highlight_text": {"renderer": "spec_text_panel", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_text_panel", "status": STATUS_READY, "notes": "M2：纯文字高亮模块，支持高亮词、字号、颜色。"},
    "module.m3_text_subsections": {"renderer": "spec_text_panel", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_text_panel", "status": STATUS_READY, "notes": "M3：父子文字模块，多个小标题 + 多段文字。"},
    "module.m4_plain_text": {"renderer": "lead_paragraph", "python": "gaming-training-poster/scripts/lib/components.py::render_lead_paragraph", "status": STATUS_READY, "notes": "M4：无底框提示文字，可插在模块之间。"},
    "module.m5_text_table": {"renderer": "data_table", "python": "gaming-training-poster/scripts/lib/components.py::render_data_table", "status": STATUS_READY, "notes": "M5：文字 + 表格，适合日程、安排、活动简介。"},
    "module.m6_image_text_single": {"renderer": "spec_image_text_split", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_text_split", "status": STATUS_READY, "notes": "M6：单图图文，支持上文下图/上图下文/左右图文。"},
    "module.m7_image_text_subsections": {"renderer": "spec_feedback_story_flow", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_feedback_story_flow", "status": STATUS_READY, "notes": "M7：图文父子模块，每个子模块可独立选择图文版式。"},
    "module.m8_single_image_text": {"renderer": "spec_image_text_split", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_text_split", "status": STATUS_READY, "notes": "M8：文字 + 单张图片，适合二维码、介绍。"},
    "module.m9_multi_image_text": {"renderer": "spec_feedback_story_flow", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_feedback_story_flow", "status": STATUS_READY, "notes": "M9：文字 + 多图，适合奖品展示、项目全景。"},
    "module.m10_single_person_card": {"renderer": "spec_course_card_list", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list", "status": STATUS_READY, "notes": "M10：单人卡片，左图右结构化文字。"},
    "module.m11_person_cards_row": {"renderer": "spec_avatar_group_wall", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_avatar_group_wall", "status": STATUS_READY, "notes": "M11：多张单人头像卡片，可一行并排展示。"},
    "module.m12_avatar_wall": {"renderer": "spec_avatar_group_wall", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_avatar_group_wall", "status": STATUS_READY, "notes": "M12：多人头像墙，每行 3-5 个。"},
    "module.m13_avatar_wall_groups": {"renderer": "spec_avatar_group_wall", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_avatar_group_wall", "status": STATUS_READY, "notes": "M13：多人头像墙父子模块，适合分组讲师/表彰名单。"},
    "module.m14_text_name_list": {"renderer": "spec_text_panel", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_text_panel", "status": STATUS_READY, "notes": "M14：纯文字名单排列，适合大量学员名单。"},
    "module.m15_text_name_list_groups": {"renderer": "spec_text_panel", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_text_panel", "status": STATUS_READY, "notes": "M15：父子纯文字名单，适合按部门/班级分组。"},
    "module.m16_course_speaker_split": {"renderer": "spec_course_card_list", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list", "status": STATUS_READY, "notes": "M16：课程卡片，左讲师头像/简介 + 右课程介绍。"},
    "module.m17_course_text_speaker": {"renderer": "spec_course_card_list", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list", "status": STATUS_READY, "notes": "M17：课程卡片，上文字介绍，下讲师头像和简介。"},
    "module.m18_course_parent_children": {"renderer": "spec_course_card_list", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_course_card_list", "status": STATUS_READY, "notes": "M18：多课程父子模块，每门课程一个子卡片。"},
    "module.m19_rating_bars": {"renderer": "spec_rating_bars", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_rating_bars", "status": STATUS_READY, "notes": "M19：课程评分积分条。"},
    "module.m20_single_image": {"renderer": "spec_image_grid", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_grid", "status": STATUS_READY, "notes": "M20：纯图片单张，适合复杂内容或大图。"},
    "module.m21_multi_image_collage": {"renderer": "spec_image_grid", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_grid", "status": STATUS_READY, "notes": "M21：多图拼盘，适合活动剪影和奖品展示。"},
    "module.m22_button_inside": {"renderer": "spec_action_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_action_bar", "status": STATUS_READY, "notes": "M22：模块内按钮，桥接时可放入模块 actions。"},
    "module.m23_button_outside": {"renderer": "spec_action_bar", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_action_bar", "status": STATUS_READY, "notes": "M23：模块外独立 CTA 按钮。"},
    "module.m24_contact_text": {"renderer": "contact_inline", "python": "gaming-training-poster/scripts/lib/components.py::render_contact_inline", "status": STATUS_READY, "notes": "M24：底部联系方式文字，无底框、无标题。"},
    "module.m25_contact_qr": {"renderer": "spec_image_text_split", "python": "gaming-training-poster/scripts/lib/components.py::render_spec_image_text_split", "status": STATUS_READY, "notes": "M25：联系方式二维码，支持二维码图片 + 说明文字。"},
})

LEGACY_MODULE_ALIASES = {
    "module.hero_title": "module.tm1_tm13_visual_layer",
    "module.theme_hero": "module.tm1_tm13_visual_layer",
    "module.theme_hero_review": "module.tm1_tm13_visual_layer",
    "module.series_identity": "module.tm1_tm13_visual_layer",
    "module.series_identity_feedback": "module.tm1_tm13_visual_layer",
    "module.logo_endorsement": "module.tm1_tm13_visual_layer",
    "module.project_background": "module.m1_text",
    "module.project_overview": "module.m1_text",
    "module.project_content": "module.m3_text_subsections",
    "module.project_recap": "module.m1_text",
    "module.completion_response": "module.m1_text",
    "module.closing_blessing": "module.m4_plain_text",
    "module.training_goals": "module.m2_highlight_text",
    "module.share_outline": "module.m3_text_subsections",
    "module.share_recap": "module.m1_text",
    "module.event_summary": "module.m5_text_table",
    "module.signup_notice": "module.m2_highlight_text",
    "module.core_question": "module.m2_highlight_text",
    "module.next_preview": "module.m2_highlight_text",
    "module.series_next": "module.m2_highlight_text",
    "module.faculty_grid": "module.m12_avatar_wall",
    "module.guest_profile_deep": "module.m10_single_person_card",
    "module.agenda_table": "module.m5_text_table",
    "module.signup_cta": "module.m23_button_outside",
    "module.replay_cta": "module.m23_button_outside",
    "module.qa_interview": "module.m3_text_subsections",
    "module.project_timeline": "module.m5_text_table",
    "module.full_timeline": "module.m5_text_table",
    "module.photo_collage": "module.m21_multi_image_collage",
    "module.group_photo": "module.m20_single_image",
    "module.course_matrix": "module.m5_text_table",
    "module.course_rating": "module.m19_rating_bars",
    "module.rating_summary": "module.m19_rating_bars",
    "module.event_multidim_rating": "module.m19_rating_bars",
    "module.student_voice": "module.m7_image_text_subsections",
    "module.feedback_gain_suggestion": "module.m7_image_text_subsections",
    "module.work_showcase": "module.m21_multi_image_collage",
    "module.mentor_quote": "module.m3_text_subsections",
    "module.course_card": "module.m18_course_parent_children",
    "module.course_feedback_card": "module.m18_course_parent_children",
    "module.course_feedback_schema": "module.m7_image_text_subsections",
    "module.series_intro": "module.m1_text",
}


def canonical_script_key(script_key: str) -> str:
    return LEGACY_MODULE_ALIASES.get(script_key, script_key)


for _legacy_key in LEGACY_MODULE_ALIASES:
    MODULE_LABELS.pop(_legacy_key, None)
    MODULE_CAPABILITIES.pop(_legacy_key, None)


def _capability_for(script_key: str, component: str | None = None) -> dict:
    canonical_key = canonical_script_key(script_key)
    module_cap = deepcopy(MODULE_CAPABILITIES.get(canonical_key) or {})
    base = module_cap.pop("base", None)
    base_cap = deepcopy(RENDERER_CAPABILITIES.get(base or component or "") or {})
    merged = {**base_cap, **module_cap}
    renderer = merged.get("renderer") or component or base
    status = merged.get("status") or STATUS_MISSING
    return {
        "script_key": script_key,
        "canonical_script_key": canonical_key,
        "label": MODULE_LABELS.get(canonical_key) or MODULE_LABELS.get(script_key) or "自定义模块",
        "renderer": renderer,
        "python": merged.get("python"),
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "notes": merged.get("notes") or "尚未登记能力，需要补齐 Python 脚本和 schema。",
    }


def enrich_module(module: dict) -> dict:
    enriched = deepcopy(module)
    canonical_key = canonical_script_key(str(enriched.get("script_key") or ""))
    if canonical_key != enriched.get("script_key"):
        enriched["legacy_script_key"] = enriched.get("script_key")
        enriched["script_key"] = canonical_key
        enriched["name"] = MODULE_LABELS.get(canonical_key) or enriched.get("name")
    capability = _capability_for(
        str(enriched.get("script_key") or ""),
        str(enriched.get("component") or ""),
    )
    enriched["capability"] = capability
    enriched["status"] = capability["status"]
    enriched["status_label"] = capability["status_label"]
    return enriched


def enrich_strategy(strategy: dict) -> dict:
    enriched = deepcopy(strategy)
    modules = [enrich_module(m) for m in enriched.get("module_plan", [])]
    enriched["module_plan"] = modules
    enriched["capability_summary"] = summarize_modules(modules)
    return enriched


def summarize_modules(modules: list[dict]) -> dict:
    counts = {STATUS_READY: 0, STATUS_NEEDS_ENHANCEMENT: 0, STATUS_MISSING: 0}
    for module in modules:
        status = module.get("status") or STATUS_MISSING
        counts[status] = counts.get(status, 0) + 1
    total = sum(counts.values())
    return {
        "total": total,
        "ready": counts.get(STATUS_READY, 0),
        "needs_enhancement": counts.get(STATUS_NEEDS_ENHANCEMENT, 0),
        "missing": counts.get(STATUS_MISSING, 0),
        "ready_ratio": round(counts.get(STATUS_READY, 0) / total, 3) if total else 0,
    }


def list_registry() -> dict:
    return {
        "version": "poster_module_registry.v1",
        "status_labels": STATUS_LABELS,
        "renderer_capabilities": RENDERER_CAPABILITIES,
        "module_capabilities": {
            key: _capability_for(key)
            for key in sorted(k for k in MODULE_CAPABILITIES.keys() if k.startswith("module.m") or k.startswith("module.tm"))
        },
    }
