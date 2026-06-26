# Module Library · 每模块的可挑排版变体（v0.9）

> 思路：模块库是"积木盒"，**每块积木提供 2~3 种形态**，拼装时按数据规模 / 风格诉求挑款。
> 同一模块的不同形态优先用 `layout` 字段切换，**不要新建模块**。

---

## Logo 位

### 顶部 logo bar

```jsonc
{ "type": "logo_bar", "position": "top",
  "variant": "white",                 // black | white | color
  "logos": ["assets/logos/tencent-ieg-horizontal-white.png"],
  "target_height": 56,
  "align": "left"                     // left | center | right
}
```

### 底部 logo bar（多 logo 一字排）

```jsonc
{ "type": "footer_logobar",
  "logos": ["…/p1.png", "…/p2.png", "…/p3.png"],
  "target_height": 48,
  "spacing": 56,
  "align": "center"
}
```

**选色判定**：
- 海报底色 hex 转灰度 ≥ 200（浅底）→ `black` / `color`
- ≤ 80（深底）→ `white`
- 中间值 / AI 复杂底图 → `white` 加 `bg_strip`（在 logo 区拉一条深色衬条）

---

## 0. 整张底图（bg layer）

### 0a. gradient-2（最常用，可控性最高）

```jsonc
"canvas": { "bg_strategy": "gradient-2",
  "bg_colors": ["#241B5C", "#0F0A2E"],
  "glow": true, "glow_top_color": "#FBBF24",
  "pattern": "grid", "grain": true }
```

### 0b. solid（极简纯色）

```jsonc
"canvas": { "bg_strategy": "solid", "bg_color": "#0E0E12",
  "pattern": "dots", "grain": false }
```

### 0c. ai-soft（AI 主题底图作顶部 band，下方接渐变）

```jsonc
"canvas": { "bg_strategy": "ai-soft",
  "bg_image": "output/ai_bg_red_packet.png",
  "bg_image_height": 760,
  "bg_image_crop_top": 0.04,
  "bg_image_crop_bottom": 0.56,
  "bg_image_y_align": "top",
  "bg_image_blend_h": 280,
  "bg_colors": ["#C8102E", "#FF7A00"],   // 下方渐变接续
  "pattern": null, "grain": false        // AI 底图时必关
}
```

---

## 1. 大标题 + 主 KV

### 1a. ai_wordart（默认，最炫，最稳）

```jsonc
{ "type": "hero_strip",
  "title_card": { "style": "ai_wordart",
    "lines": ["2026 新春训练营"],
    "subtitle": "迎新启航 · 共赴星辰大海",
    "wordart_style": "festival_red",   // 6 风格之一
    "wordart_w": 1000, "wordart_h": 240
  },
  "hero_visual": { "image": "output/red_packet.png",
    "position": "right", "scale": 0.45 }
}
```

### 1b. screen（黑屏卡 + 黄边 + 黄字外发光）

```jsonc
"title_card": { "style": "screen", "lines": ["IF 计划", "调查问卷"] }
```

### 1c. gradient-large（无卡片底，大字渐变填充 + 外发光）

```jsonc
"title_card": { "style": "gradient-large",
  "lines": ["AI 引擎论坛"],
  "color_a": "#FFE082", "color_b": "#FF7043" }
```

### 1d. ribbon（黄丝带 + 黑描边，颁奖隆重感）

```jsonc
"title_card": { "style": "ribbon", "lines": ["年度之星"] }
```

### 1e. numbered（半透明大数字 + 标题 + 装饰线，去框最干净）

```jsonc
"title_card": { "style": "numbered", "index": 1,
  "lines": ["管理者训练营"], "subtitle": "Leadership Bootcamp" }
```

---

## 2. 小标题（section_title_bar）

### 2a. numbered（推荐，去框）

```jsonc
{ "type": "section_title_bar", "style": "numbered", "index": 1,
  "text": "项目背景", "accent_color": "#FBBF24" }
```

### 2b. neon（霓虹外发光，赛博/技术场景）

```jsonc
{ "type": "section_title_bar", "style": "neon", "text": "课程内容" }
```

### 2c. ribbon（丝带）/ screen（黑屏）

```jsonc
{ "type": "section_title_bar", "style": "ribbon", "text": "讲师团" }
{ "type": "section_title_bar", "style": "screen", "text": "注意事项" }
```

---

## 3. 项目背景

### 3a. lead_paragraph + frosted（默认，一段话）

```jsonc
{ "type": "lead_paragraph", "panel_style": "frosted",
  "text": "新鹅你好，欢迎选择并加入腾讯互娱…" }
```

### 3b. info_card + heading（带小标题嵌入，3 模块自带标题）

```jsonc
{ "type": "info_card", "heading": "关于"IF 计划"",
  "body": ""IF 计划"是面向 IEG 所有技术毕业生定制的培养项目【必修】…",
  "panel_style": "frosted" }
```

### 3c. lead_paragraph + yellow-card（高亮致辞，喜庆类）

```jsonc
{ "type": "lead_paragraph", "panel_style": "yellow-card",
  "text": "致全体新春集训营成员：…" }
```

---

## 4. 项目目标 / 你将收获

### 4a. info_card + 编号正文（默认，"1. 2. 3."自动拆行）

```jsonc
{ "type": "info_card", "heading": "你将收获",
  "body": "1. 系统掌握 UE5 引擎核心模块的设计原理\n2. 完成一个完整 demo 项目并获得资深讲师反馈\n3. 与 IEG 一线技术专家建立长期连接",
  "panel_style": "frosted" }
```

### 4b. bullet_points_block（大块项目符号，不拆小卡）

```jsonc
{ "type": "info_card", "heading": "解决问题",
  "bullets": ["新人融入慢、缺技术框架体系", "缺少与一线专家的真实链接", "项目落地能力不足"],
  "panel_style": "yellow-card" }
```

### 4c. benefit_grid（4 格图标 + 标题 + 一句话，视觉密度最高）

```jsonc
{ "type": "benefit_grid",
  "items": [
    { "icon": "assets/icons/skill.png", "title": "技术体系", "desc": "12 大模块系统化覆盖" },
    { "icon": "assets/icons/network.png", "title": "人脉网络", "desc": "对接 30+ 专家" },
    { "icon": "assets/icons/output.png", "title": "项目产出", "desc": "1 个完整 demo" },
    { "icon": "assets/icons/cert.png", "title": "认证背书", "desc": "结业证书 + 内部荣誉" }
  ] }
```

---

## 5. 项目内容 / 课程安排

### 5a. curriculum_timeline（推荐，2~4 节课）

```jsonc
{ "type": "curriculum_timeline", "connector_style": "dot",
  "parts": [
    { "label": "Part 1",
      "time": "2026.06.01 19:00", "format": "线上直播",
      "topic": "UE5 渲染管线深入", "output": "课后小测" },
    { "label": "Part 2",
      "time": "2026.06.08 19:00", "format": "线下实操",
      "topic": "Demo 项目搭建", "output": "提交 demo 工程" }
  ] }
```

### 5b. schedule_table（5+ 节，表格化）

```jsonc
{ "type": "schedule_table",
  "columns": ["周次", "时间", "课题", "讲师"],
  "rows": [
    ["W1", "周一 19:00", "游戏引擎入门", "张三"],
    ["W2", "周一 19:00", "渲染基础", "李四"]
  ] }
```

### 5c. meta_row（关键信息浮于课表前，黄底卡片横排）

```jsonc
{ "type": "meta_row", "items": [
  { "icon": "assets/icons/cal.png", "label": "日期", "value": "2026.06.01-08.30" },
  { "icon": "assets/icons/loc.png", "label": "地点", "value": "深圳总部 + 线上" },
  { "icon": "assets/icons/audience.png", "label": "面向", "value": "IEG 全员" }
] }
```

---

## 6. 讲师资源

### 6a. faculty_grid · detail（≤2 人，大头像 + 长 bio）

```jsonc
{ "type": "faculty_grid", "layout": "detail", "avatar_shape": "circle",
  "members": [
    { "avatar": "…/zhangsan.png", "name": "张三",
      "title": "腾讯互娱 IEG 渲染专家",
      "bio": "10 年游戏引擎开发经验，主导 3 款 3A 项目渲染管线…" }
  ] }
```

### 6b. faculty_grid · compact（3~4 人，2 列对照）

```jsonc
{ "type": "faculty_grid", "layout": "compact", "avatar_shape": "square",
  "members": [
    { "avatar": "…/a.png", "name": "张三", "title": "渲染专家", "bio": "…" },
    { "avatar": "…/b.png", "name": "李四", "title": "AI 专家", "bio": "…" },
    { "avatar": "…/c.png", "name": "王五", "title": "TA Lead", "bio": "…" },
    { "avatar": "…/d.png", "name": "赵六", "title": "Engine TL", "bio": "…" }
  ] }
```

### 6c. faculty_grid · default（5+ 人，纵列简介）

```jsonc
{ "type": "faculty_grid", "layout": "default", "avatar_shape": "circle",
  "members": [/* 5+ 项 */] }
```

### 6d. 5+6 合并形态（课程少+讲师少，时间轴节点旁挂头像）

```jsonc
{ "type": "curriculum_timeline", "with_faculty": true,
  "parts": [
    { "label": "Part 1", "time": "06.01", "topic": "UE5",
      "faculty": { "avatar": "…/a.png", "name": "张三", "title": "渲染专家" } }
  ] }
```

---

## 7. 注意事项

### 7a. notice_box · inline（推荐，作为正文内块出现，无独立标题栏）

```jsonc
{ "type": "notice_box", "inline": true, "accent_color": "#F97316",
  "bullets": ["全程脱产，不得迟到", "需自备笔记本电脑", "缺勤 ≥2 次取消结业资格"] }
```

### 7b. rules_box · standalone（独立卡 + heading，仅当注意事项篇幅大时用）

```jsonc
{ "type": "rules_box", "heading": "请注意",
  "bullets": ["…"] }
```

---

## 8. 报名按钮

### 8a. cta_button（默认，单行大按钮）

```jsonc
{ "type": "cta_button", "text": "立即加入", "href": "https://…" }
```

### 8b. info_card_with_qr（QR + 截止时间 + 名额，培训海报最常用）

```jsonc
{ "type": "info_card_with_qr",
  "heading": "扫码报名",
  "body": "截止时间：2026.05.30 23:59\n名额：限 50 人，先到先得",
  "qr_image": "assets/qr/signup.png",
  "qr_label": "报名二维码" }
```

---

## 9. 联系方式

### 9a. contact_inline（推荐，单行字）

```jsonc
{ "type": "contact_inline",
  "text": "如有任何疑问可联系企业大学 dorrainzeng（曾子河）。" }
```

### 9b. contact_card（带二维码，正式项目用）

```jsonc
{ "type": "contact_card",
  "text": "有任何疑问，欢迎联系：",
  "contacts": [
    { "name": "龙星竹", "qr": "assets/qr/contact1.png", "role": "项目经理" },
    { "name": "李浩祯", "qr": "assets/qr/contact2.png", "role": "讲师协调" }
  ] }
```

---

## 拼装清单（cheat sheet）

最常用的"项目通知邮件海报"4 种典型组合：

### A. 完整版（10 模块全开，长图）

```
top_logo → 0 bg → 1 hero(ai_wordart) → 2+3 背景 → 2+4 收获(benefit_grid) →
2+5 课程(timeline 4 节) → 2+6 讲师团(compact) → 7 inline 注意 →
8 cta+QR → 9 contact_inline → bottom_logo
```

### B. 中量版（去掉部分小标题 / 合并 5+6）

```
top_logo → 0 bg → 1 hero → 3 lead_paragraph → 4 bullet_points_block →
5+6 timeline_with_faculty(2 节 2 讲师) → 7 inline → 8 cta+QR → 9 inline
```

### C. 极简版（仅通知核心信息）

```
0 bg → 1 hero(numbered) → 3 lead_paragraph → 5 meta_row → 8 cta_button → 9 inline
```

### D. 表彰 / 致辞类（无课程无讲师）

```
top_logo → 0 bg → 1 hero(ribbon) → 3 lead_paragraph(yellow-card) →
4 benefit_grid("我们一起做到了…") → 9 contact_card → bottom_logo
```

---

## 演进规则

- 新增模块前先翻这份文档：能用现有模块 + `layout` 字段切换吗？
- 模块的新形态先在这里加一节"5x. xxx"，再去 `components.py` 实现
- 当某个模块的形态 ≥4 种 → 考虑拆成两个模块 / 评估冗余
