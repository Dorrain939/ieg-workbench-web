"""Poster strategy rules derived from the project-group poster KB plan."""
from __future__ import annotations

PROJECT_TYPES = [
    {"id": "A", "label": "类型A · 培养项目型", "short_label": "培养项目型", "description": "长期、多轮次、有结项/毕业概念", "persuasion_strategy": "蓝图+数据+成果", "style_strategy": "brand_unified", "style_label": "品牌统一风格", "allowed_scenes": ["S1", "S2", "S3", "S4"]},
    {"id": "B", "label": "类型B · 系列活动型 / 主题多变", "short_label": "系列活动 · 主题多变", "description": "每期主题不同，通知与回顾必须风格一致", "persuasion_strategy": "破题+背书+稀缺", "style_strategy": "theme_adaptive", "style_label": "主题化风格", "allowed_scenes": ["S5a", "S5b"]},
    {"id": "C", "label": "类型C · 系列活动型 / 主题统一", "short_label": "系列活动 · 主题统一", "description": "主题领域固定，每期课程不同，强调课程矩阵和按课报名", "persuasion_strategy": "矩阵+实用+便利", "style_strategy": "series_unified", "style_label": "系列统一风格", "allowed_scenes": ["S6a", "S6b"]},
]
PROJECT_TYPE_MAP = {x["id"]: x for x in PROJECT_TYPES}

def mod(mid, name, purpose, required, component, script_key):
    return {"id": mid, "name": name, "purpose": purpose, "required": required, "component": component, "script_key": script_key, "status": "script_pending", "input_schema_key": f"input.{script_key}", "qa_rules_key": f"qa.{script_key}"}

def tm(mid="TM-ALL", name="TM1-TM13 标题区视觉层", purpose="管理标题区、Logo、底图、艺术字和模块装饰"):
    return mod(mid, name, purpose, True, "hero_strip", "module.tm1_tm13_visual_layer")

SCENES = {
    "S1": {"label": "S1 · 开班/招募海报", "project_type": "A", "node": "培养项目启动前", "goal": "吸引加入长期项目", "logic_chain": "Why → What → How → Who → When → CTA", "density": "高", "module_count_hint": "8-11 个模块", "copy_template_keys": ["slogan_training", "module_labels_s1", "cta_signup"], "design_elements": ["E-I1", "E-I2", "E-I3", "E-I4", "E-I9", "E-I10"], "style_tokens": {"palette": "brand_blue_orange", "layout": "brand_unified", "radius": 12}, "modules": [
        tm("TM-S1"), mod("M1-S1", "项目背景", "回答为什么", True, "spec_text_panel", "module.m1_text"), mod("M2-S1", "培养目标/报名要求", "回答学什么与报名条件", True, "spec_text_panel", "module.m2_highlight_text"), mod("M3-S1", "项目内容", "回答怎么学", True, "spec_text_panel", "module.m3_text_subsections"), mod("M5-S1", "项目周期/第一次集中安排", "提供行动指引", True, "data_table", "module.m5_text_table"), mod("M12-S1", "讲师阵容", "建立信任背书", True, "spec_avatar_group_wall", "module.m12_avatar_wall"), mod("M2B-S1", "温馨提示", "降低行动门槛", True, "spec_text_panel", "module.m2_highlight_text"), mod("M23-S1", "报名按钮", "促进行动", False, "spec_action_bar", "module.m23_button_outside")]},
    "S2": {"label": "S2 · 阶段总结海报", "project_type": "A", "node": "每轮集中后，非末次", "goal": "展示单阶段培训效果并延续期待", "logic_chain": "成果展示 → 氛围呈现 → 下期预告", "density": "中高", "module_count_hint": "8 个左右", "copy_template_keys": ["module_labels_s2", "score_s2", "student_quote"], "design_elements": ["E-I8", "E-I5", "E-I6", "E-I7", "E-I3", "E-I10"], "style_tokens": {"palette": "brand_blue_orange", "layout": "brand_unified", "radius": 12}, "modules": [
        tm("TM-S2"), mod("M1-S2", "完成回应", "情绪衔接", True, "spec_text_panel", "module.m1_text"), mod("M3-S2", "项目背景简述/嘉宾访谈", "快速唤起认知并增加深度", False, "spec_text_panel", "module.m3_text_subsections"), mod("M19-S2", "课程反馈", "用数据证明质量", True, "spec_rating_bars", "module.m19_rating_bars"), mod("M7-S2", "学员之声", "用情感证明价值", True, "spec_feedback_story_flow", "module.m7_image_text_subsections"), mod("M21-S2", "现场剪影", "呈现真实氛围", True, "spec_image_grid", "module.m21_multi_image_collage"), mod("M2-S2", "下期预告", "保持学员粘性", True, "spec_text_panel", "module.m2_highlight_text")]},
    "S3": {"label": "S3 · 全面回顾/结项海报", "project_type": "A", "node": "最后一轮集中/结项答辩后", "goal": "全景回顾项目并完成仪式化收尾", "logic_chain": "全景回顾 → 成果验收 → 温情收尾", "density": "很高", "module_count_hint": "10-12 个模块", "copy_template_keys": ["module_labels_s3", "score_s3", "mentor_quote", "closing_blessing"], "design_elements": ["E-I14", "E-I5", "E-I12", "E-I6", "E-I11", "E-I7", "E-I13", "E-I10"], "style_tokens": {"palette": "brand_blue_orange", "layout": "brand_unified", "radius": 12}, "modules": [
        tm("TM-S3"), mod("M1-S3", "项目概述", "唤起全貌认知", True, "spec_text_panel", "module.m1_text"), mod("M5-S3", "回顾历程时间轴", "完整学习旅程", True, "data_table", "module.m5_text_table"), mod("M19-S3", "课程反馈汇总", "全量数据总结质量", True, "spec_rating_bars", "module.m19_rating_bars"), mod("M21A-S3", "实战&验收成果", "展示学员产出", False, "spec_image_grid", "module.m21_multi_image_collage"), mod("M7-S3", "学员心声/导师寄语", "多维呈现收获并增加仪式感", True, "spec_feedback_story_flow", "module.m7_image_text_subsections"), mod("M21B-S3", "精彩瞬间/大合影", "培训氛围和收尾仪式感", True, "spec_image_grid", "module.m21_multi_image_collage"), mod("M4-S3", "底部祝福语", "项目画句号", True, "lead_paragraph", "module.m4_plain_text")]},
    "S4": {"label": "S4 · 成果展示海报", "project_type": "A", "node": "成果发布", "goal": "展示学员作品和项目成果", "logic_chain": "待知识库补充", "density": "待定", "module_count_hint": "预留", "copy_template_keys": [], "design_elements": [], "style_tokens": {"palette": "brand_blue_orange", "layout": "brand_unified", "radius": 12}, "modules": [], "status": "reserved"},
    "S5a": {"label": "S5a · 主题分享通知海报", "project_type": "B", "node": "单次分享活动预告", "goal": "吸引报名单场主题分享", "logic_chain": "破题 → 抛问 → 嘉宾/内容 → 报名", "density": "中", "module_count_hint": "7-8 个模块", "copy_template_keys": ["s5_hook_intro", "slogan_single_event", "cta_signup"], "design_elements": ["E-I17", "E-I15", "E-I16", "E-I18", "E-I9", "E-I19", "E-I10"], "style_tokens": {"palette": "theme_by_keyword", "layout": "theme_adaptive", "radius": 8}, "modules": [
        tm("TM-S5a"), mod("M1-S5a", "破题引入", "制造共鸣与兴趣", True, "spec_text_panel", "module.m1_text"), mod("M2-S5a", "核心问题/悬念", "激发好奇心", False, "spec_text_panel", "module.m2_highlight_text"), mod("M10-S5a", "嘉宾详介", "建立权威背书", True, "spec_course_card_list", "module.m10_single_person_card"), mod("M3-S5a", "分享内容概述", "明确收获预期", True, "spec_text_panel", "module.m3_text_subsections"), mod("M5-S5a", "活动信息摘要", "提供行动依据", True, "data_table", "module.m5_text_table"), mod("M23-S5a", "CTA 引导", "降低报名门槛", True, "spec_action_bar", "module.m23_button_outside")]},
    "S5b": {"label": "S5b · 主题分享回顾海报", "project_type": "B", "node": "单次分享活动结束后", "goal": "展示活动成果并沉淀回放内容", "logic_chain": "实际内容 → 多维评分 → 分类反馈 → 活动剪影", "density": "中高", "module_count_hint": "8-9 个模块", "copy_template_keys": ["module_labels_s5b", "score_multidim", "feedback_gain_suggestion"], "design_elements": ["E-I17", "E-I16", "E-I25", "E-I23", "E-I24", "E-I7", "E-I10"], "style_tokens": {"palette": "inherit_s5a_theme", "layout": "theme_adaptive", "radius": 8}, "modules": [
        tm("TM-S5b"), mod("M1-S5b", "分享回顾", "实际分享内容", True, "spec_text_panel", "module.m1_text"), mod("M10-S5b", "嘉宾信息", "权威背书", True, "spec_course_card_list", "module.m10_single_person_card"), mod("M23-S5b", "回放入口", "覆盖未到场受众", True, "spec_action_bar", "module.m23_button_outside"), mod("M19-S5b", "分享反馈评分", "多维评分", True, "spec_rating_bars", "module.m19_rating_bars"), mod("M7-S5b", "学员反馈分类", "收获与建议分栏", True, "spec_feedback_story_flow", "module.m7_image_text_subsections"), mod("M21-S5b", "活动剪影", "真实氛围", True, "spec_image_grid", "module.m21_multi_image_collage")]},
    "S6a": {"label": "S6a · 系列课程通知海报", "project_type": "C", "node": "系列课程某期预告", "goal": "展示本期课程矩阵并支持按课报名", "logic_chain": "系列定位 → 本期菜单 → 逐课详情 → 按需报名", "density": "很高", "module_count_hint": "N 门课程 × 卡片", "copy_template_keys": ["series_identity", "course_card", "per_course_signup"], "design_elements": ["E-I21", "E-I22", "E-I20", "E-I9", "E-I19", "E-I10"], "style_tokens": {"palette": "series_cyber_green", "layout": "series_unified", "radius": 10}, "hard_rules": ["每门课程卡片必须有独立报名按钮，禁止统一报名入口"], "modules": [
        tm("TM-S6a"), mod("M1-S6a", "系列简介", "说明系列价值", True, "spec_text_panel", "module.m1_text"), mod("M5-S6a", "本期课程矩阵", "课程全貌", True, "data_table", "module.m5_text_table"), mod("M18-S6a", "课程卡片 ×N", "每门课完整信息和独立报名", True, "spec_course_card_list", "module.m18_course_parent_children"), mod("M2-S6a", "系列预告/导航", "延续感", False, "spec_text_panel", "module.m2_highlight_text")]},
    "S6b": {"label": "S6b · 系列课程反馈海报", "project_type": "C", "node": "系列课程某期结束后", "goal": "逐课展示评分与反馈", "logic_chain": "系列定位 → 逐课反馈 → 延续入口", "density": "最高", "module_count_hint": "N 门课 × 反馈卡片", "copy_template_keys": ["series_identity", "course_feedback_card", "feedback_three_types"], "design_elements": ["E-I21", "E-I26", "E-I23", "E-I27", "E-I24", "E-I19", "E-I10"], "style_tokens": {"palette": "inherit_s6a_series", "layout": "series_unified", "radius": 10}, "hard_rules": ["反馈粒度必须按每门课拆分", "反馈分类必须使用亮点/收获/建议三分法"], "modules": [
        tm("TM-S6b"), mod("M18-S6b", "课程反馈卡片 ×N", "逐课数据和反馈", True, "spec_course_card_list", "module.m18_course_parent_children"), mod("M7-S6b", "反馈卡片子结构", "讲师/评分/多维/三分反馈", True, "spec_feedback_story_flow", "module.m7_image_text_subsections"), mod("M2-S6b", "系列延续入口", "往期入口/下期预告", False, "spec_text_panel", "module.m2_highlight_text")]},
}

THEME_STYLE_MAP = [
    {"keyword": "中式/国风/传统/志怪", "tone": "古雅水墨", "main": "#3c2e1e", "accent": "#5a7a5a", "decor": "山水、祥云、纸纹"},
    {"keyword": "科幻/未来/AI/技术", "tone": "赛博霓虹", "main": "#0a0a2e", "accent": "#00ffff", "decor": "电路、粒子、网格"},
    {"keyword": "艺术/美学/设计/创意", "tone": "极简文艺", "main": "#ffffff", "accent": "#222222", "decor": "留白、线性插画"},
    {"keyword": "严肃/战略/管理/商业", "tone": "极简商务", "main": "#f5f5f5", "accent": "#1a1a2e", "decor": "几何线条、数据图表"},
]

def resolve_strategy(project_type=None, scene=None):
    scene_key = scene or "S1"
    scene_rule = SCENES.get(scene_key) or SCENES["S1"]
    type_key = project_type or scene_rule["project_type"]
    type_rule = PROJECT_TYPE_MAP.get(type_key) or PROJECT_TYPE_MAP[scene_rule["project_type"]]
    if scene_key not in type_rule["allowed_scenes"]:
        scene_key = type_rule["allowed_scenes"][0]
        scene_rule = SCENES[scene_key]
    modules = list(scene_rule.get("modules", []))
    scene_payload = {k: v for k, v in scene_rule.items() if k != "modules"}
    scene_payload["id"] = scene_key
    type_payload = dict(type_rule)
    return {"project_type": type_payload, "scene": scene_payload, "module_plan": modules, "required_count": sum(1 for m in modules if m["required"]), "optional_count": sum(1 for m in modules if not m["required"]), "execution_contract_version": "poster_strategy.v1"}

def list_strategies():
    return {"project_types": PROJECT_TYPES, "scenes": {k: {kk: vv for kk, vv in v.items() if kk != "modules"} for k, v in SCENES.items()}, "theme_style_map": THEME_STYLE_MAP, "default": resolve_strategy("A", "S1")}
