# Components Catalog · 海报模块清单（v0.9 / 10 模块版）

> 抽象自用户业务侧定义的"完整结构 + 真实参考图"。
> 每加新模块前必须问：**这个模块能在 ≥2 张参考图里找到原型吗？** 不能就先不要。

## 命名约定

- 所有模块用 `snake_case`，与 brief schema 中 `type` 字段一一对应
- 模块名不带场景前缀 —— **同一模块跨场景复用**，差异由 palette / decoration_family / layout 字段调整
- 同一模块的不同形态优先用 `layout: detail | compact | default` 切换，不要为每种形态新建模块

---

## Logo 位（顶部 / 底部 二选一）

**业务定义**：`logo 顶部或者底部 一排，黑色 / 白色 / 彩色 三个版本根据背景选择`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `position` | enum | `top` / `bottom` / `none`，**顶部和底部不要同时出现** |
| `variant` | enum | `black` / `white` / `color`，与底色对比度自动选 |
| `logos[]` | string[] | logo 图片路径数组（横向一字排） |
| `target_height` | int | 默认 64，多 logo 自动等高对齐 |

**渲染器**：
- 顶部 → `hero_strip` 顶端预留位 / 或独立 `logo_bar` 段
- 底部 → `footer_logobar`

**选色逻辑**：浅底→`black` 或 `color`；深底→`white`；AI 复杂底图→优先 `white` 加底色衬条。

---

## 0. 整张底图（bg layer）

**业务定义**：渐变 / 纯色 / 符合风格需求的 AI 底图。

| 字段 | 类型 | 说明 |
|---|---|---|
| `bg_strategy` | enum | `gradient-2`（双色渐变） / `solid`（纯色） / `ai-soft`（AI 主题底图作顶部 band） |
| `bg_colors[]` | string[] | gradient-2 时填两色 |
| `bg_image` | string | ai-soft 时填 AI 出图路径 |
| `bg_image_height` | int | AI 图作顶部 band 的限定高度（推荐 760~960） |
| `bg_image_crop_top` | float | 裁掉 AI 图顶部空白比例（推荐 0~0.4） |
| `bg_image_blend_h` | int | AI 图与下方渐变的软过渡带（推荐 180~280） |
| `glow` | bool | 顶部/底部光晕 |
| `pattern` | enum | `grid` / `dots` / `null`（AI 底图时必须 null） |
| `grain` | bool | 噪点（AI 底图时必须 false） |

**渲染器**：`_draw_background`（PIL 自绘 + AI 图 cover 裁切 + alpha ramp 过渡）

---

## 1. 大标题 + 主 KV（hero_strip + ai_wordart）

**业务定义**：`大标题主标题（主KV主视觉）= 艺术字 PNG ➕ AI 主题底图 ➕ 主 KV 元素`。
**铁律**：标题艺术字必须由 AI 生成透明底 PNG 再贴入；中文绝不交给 AI 直接画在底图上。

| 字段 | 类型 | 说明 |
|---|---|---|
| `hero_image` | string | AI 出的中央插画 / 主 KV 元素（mascot/道具/红包等） |
| `hero_visual` | obj | 可选位置 left/right，缩放，裁切 |
| `title_card.style` | enum | `ai_wordart`（默认，AI 艺术字 PNG） / `screen` / `ribbon` / `gradient-large` / `numbered` |
| `title_card.lines[]` | string[] | 主标题文字（每行一条） |
| `title_card.subtitle` | string | 副标题 |
| `title_card.color_a/b` | string | gradient-large / 重染时用 |
| `title_card.recolor` | obj | `{color_a, color_b}` 仅当 AI 出黑/灰单色字 + 深底海报时用，AI 已带彩色立体字时绝对禁用 |
| `side_decor[]` | string[] | 装饰锚点：`penguin_left` / `paperplane_right` 等 |

**渲染器**：`render_hero_strip` + `scripts/gen_wordart.py`（6 风格 + 缓存）

---

## 2. 小标题 / 模块标题（section_title_bar）

**业务定义**：`每个模块前都有小标题，注意标题和模块的间距`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `style` | enum | `numbered`（推荐，半透明大数字 + 标题 + 装饰线） / `neon` / `ribbon` / `screen` |
| `text` | string | 标题文字 |
| `index` | int | numbered 样式时显示的编号 |
| `accent_color` | string | 装饰线 / 数字色 |

**渲染器**：`render_section_title_bar`

**间距铁律**：标题上方 60px，下方 24px，左右与版心同。

---

## 3. 项目背景 / 导语 / 摘要 / 致新鹅

**业务定义**：纯文字，一段话开场。

| 字段 | 类型 | 说明 |
|---|---|---|
| `text` | string | 段落文字（支持 \n 换行） |
| `panel_style` | enum | `frosted`（磨砂） / `yellow-card`（亮黄卡） / `flat`（无底） |
| `align` | enum | `left`（默认） / `center` |

**渲染器**：`render_lead_paragraph` 或 `render_info_card`（带 heading 时）

---

## 4. 项目目标 / 你将收获 / 解决痛点 / 面向人群

**业务定义**：`正文有完整段落，也有分行 1.2.3.4. 每个都应该另起一行，每个项目符号也要另起一行`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `heading` | string | 模块大标题（可选，由 section_title_bar 提供则不重） |
| `body` | string | 正文（含编号/项目符号会自动拆段） |
| `bullets[]` | string[] | 显式列条目，引擎按"大块项目符号"渲染 |
| `panel_style` | enum | `frosted` / `yellow-card` / `flat` |

**渲染器**：`render_info_card`（body 走 `_wrap_text_block` 自动按编号/项目符号拆行）

**编号识别**：`1) 1. 1、 1） (1) ① ⅠⅡ Q1: A1: · • ● ◆ ▪ ▫ ■ □ ◇ ★ ☆ ※` 共 8 类。

---

## 5. 项目内容 / 课程安排（curriculum_timeline / schedule_table）

**业务定义**：`选用时间点 / 时间轴 / 根据课程多少决定`。

### 5a. curriculum_timeline（推荐，2~4 节课）

| 字段 | 类型 | 说明 |
|---|---|---|
| `parts[]` | obj[] | 每节包含 `time / format / output / desc` |
| `connector_style` | enum | `dot`（圆点串联） / `line`（连接线） |

### 5b. schedule_table（5+ 节，表格化）

| 字段 | 类型 | 说明 |
|---|---|---|
| `columns[]` | string[] | 列头 |
| `rows[][]` | string[][] | 行数据 |

**渲染器**：`render_schedule_table` / `curriculum_timeline`

---

## 6. 讲师资源 / 嘉宾介绍（faculty_grid）

**业务定义**：`根据讲师人数决定单独介绍 vs 拼讲师团；课程少+讲师少时和 5 模块合二为一`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `members[]` | obj[] | `{avatar, name, title, bio}` |
| `layout` | enum | `detail`（≤2 人，大头像 + 长 bio） / `compact`（≤4 人 2 列） / `default`（5+ 人纵列） |
| `avatar_shape` | enum | `circle` / `square` |

**渲染器**：`render_faculty_grid`（缺头像走"首字占位"而非色块）

**5+6 合并形态**：当 `parts[].faculty` 直接挂在课程节点时，引擎不渲染独立的 faculty_grid，把头像+姓名贴在时间轴节点旁。

---

## 7. 注意事项（notice_box / rules_box）

**业务定义**：`一般是课程的强制要求 / 关键节点。可以不用单独小标题，设计上和上面区分开`。

| 字段 | 类型 | 说明 |
|---|---|---|
| `bullets[]` | string[] | 注意事项列表 |
| `inline` | bool | true=作为正文内块出现（推荐） / false=独立卡 |
| `accent_color` | string | 强调色（默认警示橙） |

**渲染器**：
- inline=true → `notice_box`（细线 + 浅底，无标题栏）
- inline=false → `rules_box`（独立卡 + heading）

---

## 8. 报名按钮（cta_button + info_card_with_qr）

**业务定义**：`点击报名按钮`。培训海报常配合报名截止 + 名额 + QR。

| 字段 | 类型 | 说明 |
|---|---|---|
| `text` | string | 按钮文字（"立即报名" / "扫码加入"） |
| `href` | string | 跳转链接（PDF 才有点击效果） |
| `qr_image` | string | 报名 QR（可选） |
| `deadline` | string | 截止时间 |
| `quota` | string | 名额信息 |

**渲染器**：`render_cta_button` + `render_info_card_with_qr` 组合

---

## 9. 联系方式（contact_inline / contact_card）

**业务定义**：`一行字的联系人企业微信，或者联系人的二维码`。

### 9a. contact_inline（推荐，单行字）

| 字段 | 类型 | 说明 |
|---|---|---|
| `text` | string | `如有任何疑问可联系xx部门 dorrainzeng（曾子河）。` |

### 9b. contact_card（带二维码）

| 字段 | 类型 | 说明 |
|---|---|---|
| `contacts[]` | obj[] | `{name, qr, role?}` |
| `text` | string | 引导语 |

**渲染器**：`render_contact_text` / `render_contact_card`

---

## 二级元素（散点装饰，不参与 section 流）

挂在全局 `decorations` 数组，引擎按密度规则自动撒点。

| type | 描述 | 适配装饰族 |
|---|---|---|
| `floating_chars` | 漂浮角色（企鹅 / 像素小人） | pixel-y2k / semi-3d-collage |
| `paper_planes` | 纸飞机 | pixel-y2k / semi-3d-collage |
| `crystals` | 冰晶碎片 | semi-3d-collage |
| `pixel_burst` | 像素粒飞溅 | pixel-y2k |
| `code_glyphs` | 代码符号 | cyber-neon |
| `spotlight` | 聚光 | ceremony-gold |
| `red_packets` | 红包 / 福字 / 鞭炮 | semi-3d-collage（festival_red 配套） |

每张图全局散点 ≤ 8 个，且必须来自同一族。

---

## 装饰族（Decoration Family）

| family | 出现于 | 风格关键词 | 配套散点装饰 |
|---|---|---|---|
| `pixel-y2k` | R1 / S1 新人训练营 | 像素描边 / 高饱和黄蓝 / 粗黑边 | floating_chars(像素), paper_planes, pixel_burst |
| `semi-3d-collage` | R2/R3 / S2 S4 S5 | 半 3D 拼贴 / 冰晶 / 紫蓝 / 暖色 | floating_chars(QQ企鹅), crystals, paper_planes, red_packets |
| `cyber-neon` | S3 S6 | 电路 / 霓虹 / 代码雨 | code_glyphs, glow_line |
| `ceremony-gold` | S5 | 聚光 / 金边 / 奖杯 | spotlight, ribbon |

每个 brief 必须显式指定 `decoration_family`，引擎据此挑装饰资产。

---

## 模块渲染契约（所有模块必须遵守）

1. **宽度**：占满版心宽（1200 - 2×margin），margin 由全局 `layout.margin_x` 决定。
2. **高度**：自适应，由模块内部根据内容计算返回（**measure-first 铁律**：先量字、后定 panel 高度）。
3. **接口**：`render(canvas, y_cursor, ctx) -> y_next`，每个模块渲染完返回新 y 游标。
4. **调色**：只能从 `ctx.palette` 取颜色，禁止硬编码。
5. **字体**：只能从 `ctx.fonts` 取（`font_path` 默认腾讯体 W3，`font_path_display` 默认腾讯体 W7），禁止 `ImageFont.truetype` 直接调用。
6. **装饰锚点**：在自己负责的区域内，可声明 `anchor_decor: ["topleft", "bottomright"]`，由引擎决定撒什么。
7. **多行正文必须走 `_wrap_text_block`**（不要用 `_wrap_text`），保证编号/项目符号每条另起一行。

---

## 防膨胀红线

- 模块总数控制在 **≤ 16 个**。新增前先问能否复用 + 用 `layout` 字段切换形态
- 视觉相似 / 字段重叠 ≥ 70% 的模块 → 合并
- 仅出现一次的特殊版式 → 走 `custom_block` 临时槽，不进目录
- **拼装时只挑用户实际需要的模块**：没素材 / 不要的模块直接跳过，不要硬塞内容
