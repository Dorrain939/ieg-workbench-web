# Brief Schema v2 · 模块化海报数据结构（v0.9）

> **思路**：先列模块清单 + 选配色，再填字段。
> 每个 v2 海报输入都按这个 schema 来；旧 schema 走 `--legacy-brief` 自动迁移。

## 顶层结构

```yaml
schema_version: 2
scene: S1 | S2 | S3 | S4 | S5 | S6 | "festival"   # 配色路由用，不再决定版式

canvas:
  width: 1200                                       # 长图固定 1200
  format: long-poster | a3-single                   # 默认 long-poster
  bg_strategy: gradient-2 | solid | ai-soft         # 三种背景策略
  bg_colors: ["#5B3FA0", "#3B2F8A"]                 # gradient-2 必填
  bg_color: "#0E0E12"                               # solid 必填
  bg_image: "output/ai_bg_xxx.png"                  # ai-soft 必填
  bg_image_height: 760                              # ai-soft 限定高度（推荐 760~960）
  bg_image_crop_top: 0.04                           # 裁掉 AI 图顶部空白比例
  bg_image_crop_bottom: 0.0                         # 裁掉 AI 图底部白模块比例
  bg_image_y_align: top | center | bottom           # 默认 top
  bg_image_blend_h: 280                             # AI 图与下方渐变软过渡带
  glow: true                                        # 顶部/底部光晕
  glow_top_color: "#FBBF24"
  glow_bottom_color: "#7C4DFF"
  pattern: grid | dots | null                       # AI 底图时必须 null
  grain: true                                       # AI 底图时必须 false
  palette_strategy: "named:festival_red"            # 12 套预设之一 / auto_bright / auto_dark / auto

decoration_family: pixel-y2k | semi-3d-collage | cyber-neon | ceremony-gold

# Brand 资产（独立于 sections，引擎自动接入 logo_bar/footer_logobar）
brand:
  logos:
    horizontal: assets/logos/tencent-ieg-horizontal-white.png
    emblem: assets/logos/tencent-ieg-emblem-white.png
    wordmark: assets/logos/tencent-ieg-wordmark-white.png
  partner_logos:
    - assets/logos/p1.png
    - assets/logos/p2.png

# Logo 位（顶部 / 底部 二选一）
logo_position: top | bottom | none
logo_variant: black | white | color

# Section 流（自上而下按需挑模块）
sections:
  # —— Logo 位会被引擎根据 logo_position 自动插入到 sections 头/尾 ——

  # 1. 大标题 + 主 KV
  - type: hero_strip
    hero_image: output/hero_xxx.png
    hero_visual: { image: "…/red_packet.png", position: "right", scale: 0.45 }
    title_card:
      style: ai_wordart | screen | ribbon | gradient-large | numbered
      lines: ["2026 新春训练营"]
      subtitle: "迎新启航 · 共赴星辰大海"
      wordart_style: festival_red                   # gen_wordart.py 6 风格之一
      color_a: "#FFE082"                            # gradient-large 用
      color_b: "#FF7043"
      recolor: { color_a: "…", color_b: "…" }       # 仅当 AI 出黑/灰单色字 + 深底时用
    side_decor: ["penguin_left", "paperplane_right"]

  # 2. 小标题（每个模块前重复用）
  - type: section_title_bar
    style: numbered | neon | ribbon | screen
    index: 1
    text: "项目背景"
    accent_color: "#FBBF24"

  # 3. 项目背景 / 导语 / 摘要
  - type: lead_paragraph
    panel_style: frosted | yellow-card | flat
    text: "新鹅你好，欢迎选择并加入腾讯互娱…"

  # 3. 替代：info_card 自带 heading
  - type: info_card
    heading: "关于'IF 计划'"
    body: "'IF 计划'是面向 IEG 所有技术毕业生定制的培养项目【必修】…"
    panel_style: frosted

  # 4. 项目目标 / 你将收获 / 解决痛点（编号正文 / bullet / benefit_grid 三态）
  - type: info_card
    heading: "你将收获"
    body: "1. 系统掌握 UE5\n2. 完成完整 demo\n3. 与一线专家建立链接"
    panel_style: frosted
  - type: info_card
    heading: "解决问题"
    bullets: ["新人融入慢", "缺技术框架", "项目落地能力不足"]
  - type: benefit_grid
    items:
      - { icon: "…", title: "技术体系", desc: "12 大模块" }

  # 5. 项目内容
  - type: curriculum_timeline
    connector_style: dot
    parts:
      - { label: "Part 1", time: "06.01 19:00", format: "线上",
          topic: "UE5 渲染管线", output: "课后小测" }
  - type: schedule_table
    columns: ["周次", "时间", "课题", "讲师"]
    rows: [["W1", "周一 19:00", "引擎入门", "张三"]]
  - type: meta_row
    items:
      - { icon: "…", label: "日期", value: "2026.06.01-08.30" }

  # 6. 讲师资源
  - type: faculty_grid
    layout: detail | compact | default
    avatar_shape: circle | square
    members:
      - { avatar: "…", name: "张三", title: "渲染专家", bio: "…" }

  # 5+6 合并形态：时间轴节点带讲师
  - type: curriculum_timeline
    with_faculty: true
    parts:
      - { label: "Part 1", time: "06.01", topic: "UE5",
          faculty: { avatar: "…", name: "张三", title: "渲染专家" } }

  # 7. 注意事项（inline 内嵌 / standalone 独立卡）
  - type: notice_box
    inline: true
    accent_color: "#F97316"
    bullets: ["全程脱产，不得迟到", "需自备笔记本"]
  - type: rules_box
    heading: "请注意"
    bullets: ["…"]

  # 8. 报名
  - type: cta_button
    text: "立即报名"
    href: "https://…"
  - type: info_card_with_qr
    heading: "扫码报名"
    body: "截止时间：2026.05.30 23:59\n名额：限 50 人"
    qr_image: assets/qr/signup.png
    qr_label: "报名二维码"

  # 9. 联系方式
  - type: contact_inline
    text: "如有任何疑问可联系企业大学 dorrainzeng（曾子河）。"
  - type: contact_card
    text: "有任何疑问，欢迎联系："
    contacts:
      - { name: "龙星竹", qr: "…", role: "项目经理" }

# 全局散点装饰
decorations:
  density: low | medium | high                      # 默认 medium = 6-8 个
  types: [floating_chars, paper_planes, crystals]   # 必须同 decoration_family
```

---

## 字段红线

- `sections[]` **顺序即渲染顺序**，引擎不重排。
- 每个 section 的 `type` 必须命中 `components-catalog.md` 中已注册的类型，否则报错。
- `decoration_family` 与 `decorations.types` 必须同族，跨族报错。
- `logo_position` 决定 logo bar 插入到 sections 头还是尾，**不要在 sections 里手动写 logo_bar**——除非有特殊位置需求。
- 长图 `canvas.format=long-poster` 时，宽度恒定 1200，高度由 sections 累加自动计算。
- `a3-single` 兼容旧版 v1 工作流，仅当 brief 显式声明时启用。
- AI 底图 (`bg_strategy=ai-soft`) 必须把 `pattern` 设为 `null`，`grain` 设为 `false`，否则糊成一片。

---

## 最小可用 brief（MVP，3 模块极简版）

```json
{
  "schema_version": 2,
  "scene": "S1",
  "canvas": {
    "width": 1200, "format": "long-poster",
    "bg_strategy": "gradient-2",
    "bg_colors": ["#5B3FA0", "#3B2F8A"],
    "palette_strategy": "named:deep_space"
  },
  "decoration_family": "semi-3d-collage",
  "logo_position": "top", "logo_variant": "white",
  "brand": {
    "logos": { "horizontal": "assets/logos/tencent-ieg-horizontal-white.png" }
  },
  "sections": [
    { "type": "hero_strip",
      "title_card": { "style": "ai_wordart", "lines": ["IF 计划"], "subtitle": "技术毕业生培养" } },
    { "type": "lead_paragraph", "panel_style": "frosted", "text": "新鹅你好…" },
    { "type": "contact_inline", "text": "如有疑问可联系企业大学 dorrainzeng（曾子河）。" }
  ]
}
```

---

## 完整版 brief（10 模块全开，长图）

见 `scripts/brief_email_notification_demo.json`（v0.9 demo），覆盖：
top_logo → hero(ai_wordart) → 项目背景 → 你将收获 → 课程时间轴 → 讲师团 →
注意事项 inline → 报名 cta+QR → contact_inline → bottom_logo。

---

## 与旧 schema 的迁移路径

旧 `title/subtitle/date/location/host/key_points/qr_code` → 新 schema：

| 旧字段 | 新位置 |
|---|---|
| title + subtitle | hero_strip.title_card.lines / subtitle |
| date / location / host | meta_row.items |
| key_points | rules_box.bullets / notice_box.bullets / qa_block.items |
| qr_code | info_card_with_qr.qr_image / contact_card.contacts |

`compose_poster_v2.py --legacy-brief` 自动迁移旧 brief。
