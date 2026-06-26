---
name: gaming-training-poster
description: 游戏大厂 IEG 培训海报生成器（v0.11.0）。当用户需要为新员工训练营、领导力项目、技术分享、文化活动、晋升发布、内部赛事等培训类活动制作长图海报时使用。支持图片素材 / 大段正文 / 表格内容三种动态输入，零占位渲染，按品牌配色出图。
agent_created: false
---

# Gaming Training Poster Skill · v0.11.0

游戏大厂 IEG 人才发展/培训部门的海报生成 Skill。
**输入：场景信息 + 素材 + 正文** → **输出：1440×N 长图海报 PNG/PDF**。

---

## 一、最常用的两条工作流（你只需要会其中一条）

### 路线 A · 直接写 brief.json（工程师风格）
```bash
# 1. 用户素材进 assets/uploads/<场景名>/
# 2. 编辑 brief.json，里面引用 uploads 路径
# 3. 渲染
python scripts/compose_poster_v2.py \
    --brief scripts/brief_<场景名>.json \
    --out output/<场景名>_v1.png
```

### 路线 B · 先写 content.md，AI 转 brief（推荐）
```bash
# 1. 用户素材进 assets/uploads/<场景名>/
# 2. 用户在 uploads 子目录里写 content.md（按文档习惯写正文）
python scripts/content_md_to_brief.py \
    --content assets/uploads/<场景名>/content.md \
    --out scripts/brief_<场景名>.json \
    --scene S4 \
    --palette named:festival_red \
    --uploads assets/uploads/<场景名>
# 3. 渲染（同路线 A 第 3 步）
```

---

## 一·五、能力分层：🔒 固定 vs 🎨 现场决定（v0.11.0 新增 · 必读）

> **核心思想**：海报生成 = 「稳定的内容载体框架」 + 「按任务现场选定的视觉变量」。
> 接到新任务时，AI 应当先核对 §1.5b 的"现场决定项"是否齐全，缺失则向用户询问或自动生成；§1.5a 的"固定能力"无需再问，直接组装。

### 1.5a · 🔒 固定能力（每次都用、无需再确认）

这些是稳定的渲染框架与组件能力，已在引擎中实现，每次新海报都直接复用：

**1. 四层图层架构**（§4.4 铁律）
   - L1 全局底图（bg_colors 渐变）/ L2 头部底图 / L3 艺术字 / L4 顶部 Logo
   - 渲染顺序、底部渐变、宽度铁律均已固化

**2. 顶部 Logo 横幅** (`top_logo_bar`)
   - logos 数组、每个独立 height、自动计算下移量、严禁重复（§8）

**3. 主标题艺术字** (`hero_strip` + `title_card`)
   - `style: ai_wordart` 模式下的 PNG 嵌入 + 抠图 + 紧贴底返回 y
   - 支持 chroma_key 黑底抠图 / 直接传透明 PNG（chroma_key=false）

**4. 副标题艺术字** (`subtitle_text`)
   - 外发光 + 主体 + 描边
   - `font_size` 自由（典型 60-160）
   - **`offset_x` 视觉居中微调**（v0.11.0）：补偿"！"等字符的视觉偏左

**5. 模块标题** (`section_title_bar`)
   - `style: plain` / `numbered`，居中大字，drop shadow

**6. 段落正文** (`lead_paragraph`)
   - **三种 panel_style**：`asset_frame`（素材框）/ `frosted` / **`none`（无框纯文字）**（v0.11.0）
   - **`font_role`** 字段（v0.11.0）：`body` (W3) / `display` (W7) 自由切换
   - 文字不溢出框（铁律）

**7. 数据表格** (`data_table`)
   - 智能列宽 + measure-first
   - **`font_size` cell 字号可配**（v0.11.0），不再硬编码 28
   - **`header_color`** 表头字色可配
   - 支持 align、col_weights、accent_color

**8. 注意事项** (`notice_box`)
   - bullets + 紫色"注意"标签
   - **bullet 支持 dict 格式**（v0.11.0）：`{"text": "...", "highlight": true, "highlight_color": "#FF4444"}` 让单条变色加粗

**9. 讲师/顾问团** (`faculty_grid`)
   - 4 种布局：`detail`（≤2大卡）/ `compact`（≤4双列）/ `default`（5+纵列）/ **`grid`（每行N人方阵）**（v0.11.0）
   - **`grid` 布局专用字段**（v0.11.0）：
     - `cols`（每行人数）、`avatar_size`、`gap_x`/`gap_y`
     - `ring_color` / `ring_width`（头像紫圈）
     - `panel_style: asset_frame` + `frame_inset`（整体加底框）
     - `name_color` / `title_color` / `title_font_role`（W3/W7 切换）
     - `max_title_lines`（限制职务最多 N 行）
     - **姓名超框时按比例自动缩小该格字号**（不影响其他格）

**10. 联系方式** (`contact_inline`)
    - **支持 `\n` 显式换行**（v0.11.0）：长文案手动分行控制视觉节奏

**11. 复杂表格** (`complex_table`) — 支持 rowspan/colspan
**12. Playwright 美观表格** (`table_module`) — 用户明确说"复杂表格图形"时启用

**13. 间距铁律**（v0.11.0 增补）
   - `hero_strip → subtitle_text` 间距 = 0（紧贴）
   - `subtitle_text → 首个 section_title_bar` 间距 = `HERO_TO_TITLE_GAP=0`
   - `section_title_bar → 其正文` 间距 = `TITLE_TO_BODY_GAP=0`
   - 其它 sections 间 = `SECTION_GAP=56`

**14. 嵌入背景层装饰系统** (`background_decorations`)（v0.11.0 新增）
    - 装饰画在 L1 全局底图之上、卡片/文字之下，**会被前景盖住**
    - 不检查禁飞区，直接全幅分布（互相避让），每素材独立 size/count/alpha/blur/rotate
    - 与原 `decorations.scatter`（表面贴纸）互补：背景嵌入用于"融入底图"，scatter 用于"前景点缀"
    - brief 字段：`brief.background_decorations.types[]`，每条 `{path, size:[min,max], count, alpha, rotate, blur}`

**15. 字体规则**
    - 主标题/数字/CTA → 腾讯体 W7（display）
    - 长段正文 → 腾讯体 W3（body），需要醒目时切 W7
    - 字体路径已固化：`assets/fonts/TencentSans-W3.ttf` / `W7.ttf`

**16. 输出规格**
    - 画布宽度固定 1440px（铁律 v0.10.1）
    - 同时输出 PNG + PDF（300dpi 标签，但本质是位图）
    - 高分辨率版本 → 用 PIL Lanczos 上采样 1.5x / 2x（PDF 不会更清晰）

---

### 1.5b · 🎨 现场决定（每次新海报必须问 / 生成 / 兜底）

接到新任务时 AI 必须依次检查以下 6 项，按"用户提供 → AI 生成 → 引擎兜底"优先级处理：

| # | 项目 | 用户可能提供 | 没提供时如何处理 |
|---|---|---|---|
| 1 | **配色方案** (`scene` + `palette_strategy`) | 直接说"紫色霓虹/朱红暖金"等 | 按主题语义自动选（赛博 → cyber_neon；新春 → festival_red；技术分享 → cyber_neon...） |
| 2 | **头部底图** (`canvas.bg_image_path`) | 上传主视觉 PNG（1440 宽最佳） | 用 ImageGen 生成 1440×800 主题底图；或仅用 bg_colors 渐变 |
| 3 | **主标题艺术字** (`hero_strip.title_card.image`) | 上传截图（任意尺寸→引擎抠图）/ 设计稿 | **优先**：PIL + 腾讯体W7 + 多层模糊光晕手工合成（稳定可控）<br>**次选**：ImageGen 生黑底艺术字 + chroma_key |
| 4 | **副标题艺术字色** | — | 跟当前配色 accent_a/b 走 |
| 5 | **段落框素材** (`asset_frame_path`) | 上传 info_frame 风格 PNG | 用 `panel_style: frosted/panel_dark/none` 兜底 |
| 6 | **装饰素材** (`background_decorations.types`) | 上传玩偶/星星/雪花/烟花... | 主题相关时让 ImageGen 生成；不需要装饰时设 `density: none` |

**询问模板**（接新任务时，AI 应主动列出"还需要确认的项"）：
> 接到 [活动主题] 海报需求。请确认：
> 1. 配色倾向？（默认按主题语义选 [xxx]）
> 2. 主视觉/头部底图？（[已收到 / 需要 AI 生成 / 用渐变兜底]）
> 3. 艺术字设计稿？（[已收到 / 需要 AI 合成 / 需要 ImageGen 生图]）
> 4. 装饰元素？（[已收到 X 个素材 / 需要 AI 生成 / 不要装饰]）
> 5. 段落框素材？（[已收到 / 用引擎自带 panel]）

---

## 二、用户上传素材规范

每次新场景**建一个 uploads 子目录**：

```
assets/uploads/lunar-new-year-2026/
├─ hero_kv.png             主视觉/装饰底图
├─ wordart.png             艺术字 PNG（透明底）
├─ mascot.png              吉祥物
├─ icon_xxx.png            图标
├─ instructor_xxx.jpg      讲师头像
├─ qr_register.png         报名二维码
└─ content.md              正文（路线 B 用）
```

文件命名小写英文连字符，**不要中文文件名**。详见 `assets/uploads/README.md`。

---

## 三、核心组件清单（按业务 10 模块编号）

| 编号 | 业务模块 | 主组件类型 | 关键字段 |
|---|---|---|---|
| 0 | 整张底图（渐变 / 纯色 / AI 主题底图） | brief.canvas | `bg_image_path`、`bg_strategy` |
| 1 | 顶部 logo 横幅 | `top_logo_bar` | `logos`、`logo_heights`、`gap` |
| 2 | 大标题 + 主 KV | `hero_strip` | `title_card.image`、`hero_mascot` |
| 3 | 副标题艺术字 | `subtitle_text` | `text`、`font_size` |
| 4 | 段落标题 | `section_title_bar` | `style: plain`、`text` |
| 5 | 项目背景 / 导语 | `lead_paragraph` | `text`、`panel_style` |
| 6 | 课程内容（复杂表格） | `complex_table` | `col_weights`、`headers`、`rows` |
| 7 | 注意事项 | `notice_box` | `bullets`、`accent_color` |
| 8 | 联系方式 | `contact_inline` | `text` |
| 9 | 通用表格 | `data_table` | `headers`、`rows`、`col_weights` |

完整组件参数见 `references/components-catalog.md`。

---

## 四、渲染铁律（v0.10.1 固化，未来通用）

> **重要区分：铁律分两类。**
>
> - **🔒 通用铁律**：所有海报项目都必须遵守，不随配色/风格变化
> - **🎨 场景灵活**：根据具体配色方案、用户交互、参考图片动态决定，不固定

---

### 🔒 通用铁律

#### 1. 零占位铁律
- 引擎**永远不画凭空几何**（小方块/小圆点/占位图等）
- 所有装饰必须由 brief 显式声明 PNG 路径
- 默认 `decorations.density = "none"`，brief 不显式打开就完全没散点

#### 2. 间距铁律
- `hero_strip(ai_wordart)` 默认 `tight_bottom=true`，return y = 艺术字底 - 60px
- `HERO_TO_TITLE_GAP = 0`、`TITLE_TO_BODY_GAP = 0`，全局已内化
- `SECTION_GAP = 56` 仅用于段落级分隔

#### 3. 字体铁律
- W7（display）= 标题/数字/CTA/艺术字
- W3（body）= 普通正文/说明/bullet 内容
- W3 太细 → 调用 `ctx.body_text_kwargs(fill)` 自动加 `stroke_width=1` 模拟伪粗

#### 4. 主视觉图层铁律（v0.10.4 重写）

海报头部视觉区由**四个独立图层**严格堆叠，顺序不可乱，缺一不可：

```
┌─────────────────────────────────────────┐
│  Layer 4：顶部 Logo 横幅（top_logo_bar）  │ ← 最顶层，压在一切之上
│  位置：海报最顶部；图层：所有内容之上     │
├─────────────────────────────────────────┤
│  Layer 3：艺术字（hero_strip.title_card）│ ← 透明底，叠在头部底图上
│  位置：头部底图中间偏下；黑底生图+抠图   │
├─────────────────────────────────────────┤
│  Layer 2：头部底图（canvas.bg_image_path）│ ← 仅覆盖头部区域，底部渐变到透明
│  宽度必须 = 画布宽（1440px）；底部渐变透明│
├─────────────────────────────────────────┤
│  Layer 1：全局底图（canvas.global_bg_*） │ ← 最底层，铺满整张海报始终到尾
│  整张海报从头到尾的背景色/纹理图层       │
└─────────────────────────────────────────┘
```

**四层职责说明：**
- **全局底图（L1）**：整张海报的背景氛围，可以是渐变色或一张竖版铺满图，覆盖整张海报高度。由 `canvas.bg_colors` 渐变或 `canvas.global_bg_path` 图片提供。
- **头部底图（L2）**：主视觉冲击区，宽度 = 1440px，高度适中（建议 600-900px），底部必须渐变到透明，让全局底图的颜色透出，实现无缝衔接。由 `canvas.bg_image_path` 提供，引擎自动按宽度缩放并在底部叠加渐变遮罩。
- **艺术字（L3）**：主标题文字图片，必须透明底（黑底生图+抠图），叠加在头部底图上方，居中略偏下。由 `hero_strip.title_card` 提供，`chroma_key=true` 自动抠黑底。
- **顶部 Logo（L4）**：品牌标识横幅，始终在最上方，不被任何底图或艺术字遮挡。由 `top_logo_bar` section 提供。

**渲染顺序铁律（代码层面）**：
```
① _draw_background() → 先铺全局底图(L1渐变) → 再贴头部底图(L2) → 立即叠底部渐变遮罩
② sections 流式渲染：top_logo_bar(L4) → hero_strip含艺术字(L3) → subtitle_text → 正文...
```

#### 5. 正文框内容不溢出铁律
- 所有正文框（`info_card`、`lead_paragraph` 等）文字必须在框内完整显示，不得溢出边界
- `asset_frame` 模式：文字颜色必须与框内背景有足够对比度，确保可读（例：淡色背景框内不能用白字）
- 九宫格拉伸的 corner 值需与素材实际圆角匹配，避免圆角变形

#### 6. 顶部 logo 横幅铁律
- **严禁**底部 `footer_logobar` 与顶部 `top_logo_bar` 同时存在（见第八节详细规范）
- `hero_strip` 中不设 `logo_slot` 字段，避免与顶部 logo 横幅重复渲染

#### 7. 复杂表格框线铁律
- colspan/rowspan 合并单元格内部不画多余格线（见第十节详细规范）

#### 8. 报名段铁律
- 直接用 `cta_button` 大居中按钮 + `pre_lines` + `post_lines`

#### 9. 底图宽度铁律（v0.10.3 新增）
- 底图（`bg_image_path`）**必须与画布同宽（1440px）**
- 引擎强制 `bg_image_fit = "width"`，不执行 contain/cover 模式
- `bg_image_max_height` 字段**无效**，不会截断高度，底图高度完全由原图比例决定
- **生图时必须指定宽度 = 1440px**（或与画布等宽），例如 `size="1440x900"`

#### 10. 底图底部渐变铁律（v0.10.4 更新）
- 底图底部**必须渐变到完全透明（alpha=0）**，让全局底图颜色自然透出，禁止渐变到背景色
- 渐变实现：在底图 alpha 通道上操作，底部 30% 区域从 alpha=255 线性降到 alpha=0
- brief 可用 `"bg_image_bottom_fade_ratio": 0.30` 调整渐变比例（默认 0.30，即底部 30%）

#### 11. 艺术字生图铁律（v0.10.3 新增）
- AI 生图艺术字**必须使用纯黑底**（`#000000`），不要透明底生图（生图工具对透明底支持不稳定）
- brief 中 `title_card.chroma_key = true`，`chroma_bg_kind = "dark"`，`key_lightness` 建议 30~40
- 引擎自动按亮度将黑色背景抠成透明，保留艺术字像素
- **禁止** `chroma_key = false` 配合黑底 RGB 图（黑底会直接覆盖底图内容）

#### 12. 副标题装饰框铁律（v0.10.3 新增）
- `subtitle_text` **默认无装饰框**，`frame_style` 默认值已在代码中固化为 `"none"`
- brief 中不得设置 `frame_style: "diamond"` 等样式，装饰框视觉效果差
- 副标题效果仅保留：外发光 + 白色字体 + accent 色描边

#### 13. 头部底图起始位置铁律（v0.10.4 新增）
- 头部底图**必须从 y=0 开始**，与海报最顶部完全平齐
- 顶部 Logo 浮在底图上方（由 sections 流式渲染顺序保证图层关系），不偏移底图
- 引擎强制 `bg_y_offset = 0`，忽略 logo bar 高度对底图位置的影响

#### 14. 副标题与大标题间距铁律（v0.10.4 新增）
- 副标题（`subtitle_text`）与大标题艺术字之间**视觉间距不超过 1cm**（约 38px）
- `tight_bottom` 始终返回 `_wordart_bottom + 8px`，不受 `band_h` 截断
- `subtitle_text` 的 `pad_top` 建议设为 `8~16px`，不得超过 20px

---

### 🎨 场景灵活（随配色/风格/用户需求变化）

以下内容**不固定**，每次海报制作需根据实际情况决定：

- **模块标题风格**：`plain`（白字下划线）/ `numbered`（数字编号）/ 其他样式，颜色跟配色方案走
- **正文框样式**：`asset_frame`（素材框）/ `frosted`（磨砂）/ `panel_dark`（深色面板），根据整体配色和用户提供的参考图决定
- **副标题艺术字颜色**：发光颜色、描边颜色跟主配色对齐，不固定为紫色
- **所有 accent_color**：表格强调色、下划线渐变色、按钮色等，均从当前配色方案取值
- **Light / Dark 模式**：由 `palette_strategy` 和用户需求决定，light 模式下 panel alpha=255 不透明（引擎自动处理）
- **是否使用 `asset_frame`**：如用户提供了特定素材框，使用素材框；否则可用引擎自带 panel

---

## 五、配色策略

通过 `brief.canvas.palette_strategy` 选配色。**必须与 `brief.scene` 同场景，否则路由覆盖后配色错乱。**

| 写法 | 对应 scene | 含义 |
|---|---|---|
| `named:aurora` | **S1** | 极光蓝紫（新人训练营） |
| `named:pixel_dawn` | **S1** | 像素暖晨光 |
| `named:nebula_blue` | **S1** | 星云蓝 |
| `named:deep_space` | **S2** | 深空藏蓝（领导力） |
| `named:charcoal_gold` | **S2** | 炭黑+金 |
| `named:cyber_neon` | **S3** | 霓虹赛博（技术分享）|
| `named:engine_core` | **S3** | 引擎核心荧光绿 |
| `named:carnival` | **S4** | 嘉年华糖果色（文化活动） |
| `named:sunset_arcade` | **S4** | 夕阳街机 |
| `named:festival_red` | **S4** | 朱红暖金（节日/新春） |
| `named:velvet_gold` | **S5** | 丝绒金（晋升表彰） |
| `named:ink_honor` | **S5** | 水墨荣耀 |
| `named:arena` | **S6** | 电竞竞技场（赛事） |
| `named:circuit_flame` | **S6** | 电路火焰 |
| `auto_bright` | 任意 | 引擎按 vibe 自动选 light 配色 |
| `auto_dark` | 任意 | 引擎按 vibe 自动选 dark 配色 |

**选配色口诀：scene 填哪个字母，`named:` 就选那个字母开头的别名。**

---

## 六、快速上手（2 步）

1. 在 `assets/uploads/` 建该场景子目录，把素材丢进去
2. 写 `brief_<场景>.json` 或 `content.md`，跑 `compose_poster_v2.py` 渲染

---

## 七、目录结构速查

```
gaming-training-poster/
├── SKILL.md                       ← 本文档
├── README.md / QUICKSTART.md
├── requirements.txt
│
├── references/                    ← 知识层（参考文档）
│
├── scripts/                       ← 引擎层（Python）
│   ├── compose_poster_v2.py           ★ 主渲染入口
│   ├── content_md_to_brief.py         content.md→brief 转换器
│   ├── brief_<场景>.json              各场景 brief
│   └── lib/                           引擎子模块
│       ├── components.py                  ★ 所有 render_xxx 渲染器
│       ├── effects.py                     视觉效果
│       ├── text_layout.py                 中文换行
│       ├── palette_lab.py                 命名配色
│       └── ...
│
├── assets/                        ← 静态素材
│   ├── fonts/                         腾讯体 W3/W7
│   ├── logos/                         IEG logo 各版本
│   └── uploads/                       ★ 用户上传素材
│
└── output/                        ← 渲染产物（PNG + PDF）
```

---

## 八、顶部 logo 横幅（top_logo_bar）排版铁律 · v0.10.1

> 适用于海报顶部展示多个品牌 logo 的横幅区域。

### 8.1 brief 字段

```json
{
  "type": "top_logo_bar",
  "logos": [
    "/绝对路径/腾讯招聘logo.png",
    "/绝对路径/互动事业群logo.png",
    "/绝对路径/IEG游戏人才招聘项目logo.png",
    "/绝对路径/IEG人力资源中心logo.png"
  ],
  "logo_height": 44,
  "logo_heights": [26, 44, 60, 44],
  "gap": 80,
  "pad_top": 20,
  "pad_bottom": 20,
  "align": "center"
}
```

### 8.2 字段说明

| 字段 | 说明 |
|---|---|
| `logos` | 必填，按顺序左→右排列的 logo PNG 路径数组 |
| `logo_height` | 通用高度（备用，当 `logo_heights` 不足时使用） |
| `logo_heights` | **关键**：为每个 logo 单独指定高度，解决不同 logo 原始宽高比差异导致的视觉不均匀问题 |
| `gap` | logo 之间水平间距，建议 60~100px |
| `pad_top` / `pad_bottom` | 上下留白，建议各 20px |
| `align` | 整体对齐方式，固定用 `"center"` |

### 8.3 排版铁律

1. **放在 sections 数组最前面**（hero_strip 之前），不得放到底部
2. **logo 必须是 RGBA 透明背景**，深色海报用白色版本 logo
3. **严禁使用底部 `footer_logobar`**：顶部 top_logo_bar 与底部 footer_logobar 二选一，两者均使用时会出现重复 logo，已确认铁律为**只用顶部**
4. **`logo_heights` 视觉均匀化**：当各 logo 原始宽高比差异悬殊（如腾讯招聘 logo 宽高比 8:1）时，必须用 `logo_heights` 逐个指定高度，使各 logo 缩放后视觉宽度接近（目标：各 logo 缩放后宽度差异 ≤ 100px）
5. **`brief.logo_position` 必须设为 `"none"`**：防止引擎自动在 top_logo_bar 之外再补一组旧 logo
6. **`hero_strip` 中不设 `logo_slot` 字段**（或不填，代码默认值已改为 `None`）：避免在主视觉区域左上角自动渲染品牌 logo，与顶部 logo 横幅重复

### 8.4 logo 文件预处理规范

- **检查组合 logo 文件**：有些 logo 文件（如 `人才招聘项目logo.png`）可能把多个 logo 拼在同一张图里，需用 PIL 按 alpha 通道扫描分割点，裁剪出单个 logo 再使用
- **验证白色 logo**：白色 logo 在白底上不可见，验证时需在红/绿底上预览确认内容正确
- **裁剪方法参考**：
```python
from PIL import Image
import numpy as np
im = Image.open("组合logo.png").convert("RGBA")
alpha_arr = np.array(im.split()[3])
col_counts = (alpha_arr > 10).sum(axis=0)
# 找连续空白列（col_counts < 2），确定分割位置
split_x = 260  # 示例：从第260列开始是空白区域
right_logo = im.crop((split_x + 190, 0, im.width, im.height))  # 裁右半
```

### 8.5 背景图偏移自动计算（compose_poster_v2.py 铁律）

当 sections 中有 `top_logo_bar` 时，背景底图会自动下移 `logo_reserved_top` 像素，公式：

```
logo_reserved_top = max(logo_heights) + pad_top + pad_bottom + 8px安全边距
```

引擎优先读 `logo_heights` 数组的最大值，不存在时读 `logo_height`。这确保背景图不会覆盖顶部 logo 区域。

---

## 九、副标题艺术字（subtitle_text）排版铁律 · v0.10.1

> 适用于主视觉艺术字下方的副标题，如"正式开营啦！"

### 9.1 brief 字段

```json
{
  "type": "subtitle_text",
  "text": "正式开营啦！",
  "font_size": 56,
  "pad_top": 8,
  "pad_bottom": 8
}
```

放在 `hero_strip` 之后、第一个 `section_title_bar` 之前。

### 9.2 渲染效果（游戏艺术字风格）

两层合成（颜色跟随配色方案，以下为示例）：
1. **外发光层**：用 accent 色文字模糊后生成光晕，高斯模糊半径 = `font_size / 6`
2. **主体层**：浅色/白色文字 + accent 色外描边，描边宽度 = `max(3, font_size // 14)`

最终视觉效果：主体文字 + 轮廓描边 + 外发光，与游戏 UI 标题艺术字风格一致。

> 🎨 **颜色灵活**：发光色、描边色均从当前配色方案的 accent_a / accent_b 取值，不固定为紫色。

### 9.3 位置要求（固定）

- `hero_strip` 启用 `tight_bottom=true` 后，返回 y 紧贴艺术字底部
- `subtitle_text` 的 `pad_top` 建议 8~20px，提供与主艺术字的安全间距
- `subtitle_text` 之后是 `SECTION_GAP=56px`，再接第一个 `section_title_bar`，间距足够

---

## 十、复杂表格（complex_table）排版规范 · v0.10.1

> 适用于课程框架、项目全景等含 rowspan/colspan 合并单元格的二维数据。

### 10.1 brief 字段

```json
{
  "type": "complex_table",
  "col_count": 7,
  "col_weights": [0.55, 0.85, 1.6, 1.25, 1.25, 1.25, 1.25],
  "accent_color": "#9333EA",
  "font_size": 22,
  "pad": 16,
  "headers": [
    {"text": "专业", "align": "center"},
    {"text": "大类", "align": "center"}
  ],
  "rows": [
    [
      {"text": "Unity 3D\n特效", "rowspan": 5, "align": "center", "bold": true},
      {"text": "课程框架", "align": "center"}
    ]
  ]
}
```

### 10.2 排版铁律

**列宽**
- `col_weights` 控制相对宽度，每列下限 = `font_size × 3`（保证至少3个字可读）
- 内容多的列（如"主要内容"）应给更大权重（1.5~2.0），标签列给小权重（0.5~0.7）

**换行**
- 使用 `wrap_cjk`，**英文单词不在单词中间断开**
- `\n` 显式换行（适合短文本强制折行）

**合并单元格框线规则**
- **竖线**：只在真实单元格边界画，colspan 覆盖的内部列不画
- **横线**：只在真实行边界画，rowspan 跨越的行底不画（引擎自动分段跳过）

**行高**
- 非跨行单元格：该行所有单元格文本高度的最大值
- 跨行单元格（rowspan>1）：确保 `sum(row_heights)` >= 单元格内容高度，不足时高度加到最后一行

**推荐 font_size**
- 7 列宽表（1440px 海报）：`font_size: 22`
- 3-4 列普通表：`font_size: 26-28`

**text_layout.py 已知 bug（v0.10.1 已修复）**
- `wrap_cjk` 遇到 `（` 等行尾禁排字符（`TAIL_FORBIDDEN`）在极窄列可能无限循环
- 修复：当去掉尾字符后 cur 为空时，强制正常换行

---

## 十、附：Playwright 美观表格插件（table_module）· v0.10.2

> **使用场景**：当你在制作前或制作中明确说明「这个模块要用复杂表格图形呈现」时，引擎使用此插件渲染——底层走 HTML→Playwright 截图，支持大圆角容器、渐变标题、分区色块等 CSS 效果，远比纯 PIL 的 complex_table 美观。两种表格组件互补，不互相替代。

### 触发规则（🔒 铁律）

- 用户在对话中主动说明「用复杂表格」「表格图形」「HTML 表格风格」时，将对应 section 的 `type` 写为 `"table_module"`
- 未明确声明时，默认用 `complex_table`（纯 PIL，无需额外依赖）

### brief 字段

```json
{
  "type": "table_module",
  "title": "课程体系",
  "theme": "purple_tech",
  "theme_overrides": {
    "border": "rgba(168,85,247,0.55)",
    "title_underline": "linear-gradient(90deg, #a855f7, #c084fc)",
    "star": "#c084fc",
    "header_bg": "#ece5f5",
    "header_text": "#2d1b4e",
    "deliv_bg": "#d3e4a3",
    "deliv_text": "#2d3b1c",
    "text": "#ffffff"
  },
  "pad_top": 32,
  "pad_bottom": 32,
  "sections": [
    {
      "tab": "第一周",
      "tab_color": "#d8c6e8",
      "columns": [
        {"header": "特效基础", "objective": "掌握粒子系统基本原理", "deliverable": "粒子作业"},
        {"header": "材质入门", "objective": "理解PBR材质流程", "deliverable": "Shader作业"}
      ],
      "review_label": "作业验收"
    }
  ]
}
```

### 配色跟随规则（🎨 场景灵活）

- `theme` 选最接近整体配色的基础主题（`purple_tech` / `blue_business` / `orange_vivid`）
- `theme_overrides` 注入海报精确颜色，可覆盖任意颜色键：

| 键 | 含义 |
|----|------|
| `border` | 容器切角边框色（支持 rgba） |
| `title_underline` | 标题下划线（支持 linear-gradient） |
| `star` | 标题两侧装饰星色 |
| `notice_icon` | 通知栏图标色 |
| `header_bg` | 表头单元格背景色 |
| `header_text` | 表头文字颜色 |
| `deliv_bg` | 交付物/验收单元格背景色 |
| `deliv_text` | 交付物/验收文字颜色 |
| `text` | 全局正文色（通常白色） |

- 只改需要调整的键，其余保持基础主题默认值

### 排版铁律

- `columns` 每个 section 最少 2 列、最多 12 列
- `tab` 文字最多 12 字符，超长会自动截断
- `objective` 最多 240 字，超长会自动截断加「…」
- `deliverable` 为空时该单元格留白，不强制填写
- `comprehensive` 字段可声明跨列「综合大作业」区域（span_from/span_to 基于1）

---

## 十一、模块标题（section_title_bar）排版铁律 · v0.10.1

### 11.1 brief 字段

```json
{
  "type": "section_title_bar",
  "style": "plain",
  "text": "项目介绍"
}
```

### 11.2 模块标题排版规范

**🔒 固定：**
- 大字（52px，W7 display 字体）+ drop shadow
- **严禁**加彩色背景框覆盖全宽（标题不能被压在色块里，要与底图融合）
- 标题文字与下划线/装饰线必须居中对齐

**🎨 灵活（随配色/风格）：**
- 字色：深色底图用白色，浅色底图用深色
- 下划线颜色：跟配色方案的 accent_a/accent_b 走（示例：深空紫配色下用 `#CC66FF` → `#8833CC` 渐变）
- 样式（`plain` / `numbered` / 其他）：由用户需求或参考图决定

---

## 十二、正文内容框排版铁律 · v0.10.1

### 12.1 panel_style 说明

正文卡片（`lead_paragraph`、`info_card`）的 panel 样式**根据配色方案灵活选择**：

| panel_style | 适用场景 | 说明 |
|---|---|---|
| `asset_frame` | 用户提供了素材框 PNG | 九宫格拉伸，视觉最精致 |
| `frosted` | 深色系配色，无素材框 | 半透明磨砂效果 |
| `panel_dark` | 深色系配色 | 纯色深底面板 |
| `panel_light` | 浅色系配色 | 浅色面板，需配深色字 |

### 12.2 🔒 通用铁律（所有 panel_style 均适用）

- **文字颜色必须与框内背景形成足够对比度**（可读性优先）
  - `asset_frame` 使用淡色/白色素材框时：文字用深色（如 `#2D0B5C` 或 `#1A0A3D`）
  - `frosted` / `panel_dark` 深底时：文字用白色或浅色
- **文字内容不得溢出框外边界**：字号、内边距、wrap 宽度需在渲染前测量
- `asset_frame` 的九宫格 corner 值需与素材实际圆角匹配

### 12.3 🎨 灵活部分

- 具体使用哪种 panel_style：根据当前配色方案和用户提供的参考图决定
- `asset_frame_path` 的素材文件：由用户提供或从历史案例选取
- 文字颜色的具体色值：在满足对比度的前提下，跟配色方案走

---

## 十三、AI 生图完整流程（🔒 必须完全自动执行，不得跳过）

> AI 必须使用内置 **ImageGen 工具**完成所有素材生图，禁止要求用户自行生图。
> 每次生成海报，必须按以下顺序生成四类素材，缺一不可。

---

### 13.1 生图执行顺序（🔒 铁律，不可跳过）

```
步骤 1：生成 全局底图（L1）
步骤 2：生成 头部底图（L2）
步骤 3：生成 艺术字·主标题（L3）
步骤 4（可选）：生成 艺术字·副标题（L3，大小约主标题 50%）
步骤 5：填写 brief.json，引用上述生成的图片路径
步骤 6：运行 compose_poster_v2.py 渲染
```

---

### 13.2 全局底图（L1）·  ImageGen 调用规范

**职责**：整张海报从头到尾的背景，渲染到最底层，覆盖整张海报高度。

```
工具：ImageGen
size：1440x2400（竖版，铺满整张长图）
prompt 要求：
  - 整体氛围背景图，颜色渐变丰富但不凌乱
  - 不含任何文字、logo、人物
  - 画面元素密度低，留出空间给上层内容
  - 风格与主题一致（嘉年华=糖果色/烟花；技术分享=电路板/粒子；等）
存储路径：assets/uploads/<场景名>/global_bg_<描述>_<时间戳>.png
brief 字段：canvas.global_bg_path（⚠️ 见 13.5 注意事项）
```

---

### 13.3 头部底图（L2）· ImageGen 调用规范

**职责**：主视觉冲击区，仅覆盖海报顶部，底部渐变透明融入全局底图。

```
工具：ImageGen
size：1440x800（横版，宽度必须 = 画布宽 1440px）
prompt 要求：
  - 主视觉场景图，画面中心留空（艺术字会叠在上方）
  - 底部颜色应与 canvas.bg_colors[1] 接近，方便渐变融合
  - 不含文字；可有游戏元素/场景装饰/光效
  - 高质量，色彩饱和，与主题高度匹配
存储路径：assets/uploads/<场景名>/hero_bg_<描述>_<时间戳>.png
brief 字段：canvas.bg_image_path
引擎处理：自动按宽度缩放 + 底部叠加渐变遮罩（bg_image_bottom_fade）
```

---

### 13.4 艺术字（L3）· ImageGen 调用规范

**职责**：主标题文字，透明底，叠在头部底图上方居中偏下。

```
工具：ImageGen
size：1440x400（宽图，文字横向展开）
prompt 要求（🔒 必须严格遵守）：
  ① 背景必须是纯黑色（pure solid black #000000 background，opaque，不透明）
  ② 文字风格：游戏大字艺术字，金色/橙色/主题色，带描边和内发光
  ③ 仅包含标题文字，不加任何装饰图形或 logo
  ④ 文字居中，留出左右边距
存储路径：assets/uploads/<场景名>/wordart_main_<描述>_<时间戳>.png
brief 字段：hero_strip.title_card.image
抠图配置（🔒 必须设置）：
  chroma_key: true
  chroma_bg_kind: "dark"
  key_lightness: 35
```

**副标题艺术字（可选，约主标题 50% 大小）：**
```
size：1440x200
prompt：同上，但文字更小更细，可用银色/白色/副色
存储路径：assets/uploads/<场景名>/wordart_sub_<描述>_<时间戳>.png
brief 字段：subtitle_text.image（或独立 hero_strip 中第二个 title_card）
```

---

### 13.5 尺寸计算器（填 brief 前先算）

引擎按**等比缩放到画布宽度**（当前 1440px），高度由原图比例决定：

```
实际渲染高度 = round(原图高 × 1440 / 原图宽)
```

| 目标 hero 高度 | 推荐生图比例 |
|---|---|
| 600px | 1440×600（12:5） |
| 736px | 1440×736（约2:1） |
| 900px | 1440×900（16:10） |

### 艺术字位置计算

```
card_y = hero.height - offset_from_bottom
约束：card_y / hero.height ∈ [0.35, 0.70]
```

---

### 13.6 ⚠️ 注意事项

- `global_bg_path` 目前代码中用 `bg_colors` 渐变兜底，若需真实图片铺满，需在 brief 额外处理或由引擎 L1 渐变替代
- 每次生成新场景，**必须全部重新生图**，不得复用其他场景的底图或艺术字
- 生图完成后执行 §14 的 Checklist 验证图片尺寸和透明度

---

## 十四、AI 生图强制 Checklist（每次生图后必须执行）

### Checklist A · 底图验证

```python
from PIL import Image
img = Image.open("生成的底图路径")
actual_hero_h = round(img.height * 1440 / img.width)
# 验证高度偏差 <= 10px
```

### Checklist B · 艺术字验证

```python
from PIL import Image
img = Image.open("生成的艺术字路径")
assert img.mode == "RGBA"
alpha_min = img.split()[3].getextrema()[0]
assert alpha_min < 10  # 透明底有效
```

**透明底获取优先级（高→低）：**
1. 生图工具传 `"background": "transparent"` 参数
2. brief 设 `"chroma_key": true`，引擎自动按亮度抠图
3. **禁止**：`chroma_key: false` + RGB 图

### Checklist C · 配色验证

```
scene 值 ——→ palette_strategy 命名必须同场景
S1 ←→ aurora / pixel_dawn / nebula_blue
S2 ←→ deep_space / charcoal_gold
S3 ←→ cyber_neon / engine_core
S4 ←→ carnival / sunset_arcade / festival_red
S5 ←→ velvet_gold / ink_honor
S6 ←→ arena / circuit_flame
```

---

## 十五、版本里程碑

- **v0.11.0**（2026-06-01）：实战增量固化
  - **能力分层架构**（§1.5）：明确 🔒 固定能力（每次都用） vs 🎨 现场决定（每次必问/生成/兜底）—— 接到新任务时按 §1.5b 的 6 项 checklist 询问用户/生成素材/落兜底
  - **`lead_paragraph` 新增 `panel_style: "none"`**：直接在底色上渲染纯文字，无任何卡片框
  - **`lead_paragraph` 新增 `font_role` 字段**：W3 (body) / W7 (display) 自由切换
  - **`notice_box` bullet 支持 dict 格式**：`{"text": "...", "highlight": true, "highlight_color": "#FF4444"}` 让单条标红加粗（用于"重点提醒"场景）
  - **`data_table` 新增 `font_size` cell 字号字段**：不再硬编码 28，`header_color` 也开放
  - **`subtitle_text` 新增 `offset_x` 字段**：视觉居中微调（补偿"！"等字符的视觉偏左）
  - **`_draw_avatar` 新增 `ring_color` / `ring_width`**：头像描边可独立配置；修复"头像盖住描边"bug，描边在头像之上保留完整
  - **`faculty_grid` 新增 `grid` 布局**：每行 N 人头像方阵（头像在上、姓名+职务在下），专门用于"内部顾问团"等 5+ 人方阵展示
    - 子字段：`cols` / `avatar_size` / `gap_x` / `gap_y` / `name_color` / `title_color` / `name_font_size` / `title_font_size` / `title_font_role` / `max_title_lines`
    - **姓名超框时按比例自动缩小该格字号**（不影响其他格）
    - 支持 `panel_style: asset_frame` + `frame_inset`（整体加底框）
  - **`contact_inline` 支持 `\n` 显式换行**：长文案手动控制视觉节奏
  - **🆕 `background_decorations` 嵌入背景层装饰系统**（§14 同名扩展）：
    - 装饰画在 L1 全局底图之上、卡片/文字之下，**会被前景盖住**（"融入底图"，区别于原 `decorations.scatter` 的"表面贴纸"）
    - 不检查禁飞区，全幅分布（互相避让）
    - 每素材独立配置：`{path, size:[min,max], count, alpha, rotate, blur}`
    - brief 字段：`brief.background_decorations.types[]`
  - **`decorations.scatter` 单素材 `size` + `count` 字段**：每个装饰素材可独立指定尺寸范围和数量
  - **间距铁律增补**：`subtitle_text → 首个 section_title_bar` 收紧为 `HERO_TO_TITLE_GAP=0`，主+副+首模块视觉成一组

- **v0.10.4**（2026-05-29）：
  - **四层图层架构铁律**：明确全局底图(L1) / 头部底图(L2) / 艺术字(L3) / 顶部Logo(L4) 四层独立概念、职责和堆叠顺序
  - **ImageGen 生图流程固化**：AI 必须使用 ImageGen 工具按顺序生成全局底图→头部底图→艺术字，不得跳过，不得要求用户自行生图
  - **头部底图起始位置铁律**（§13）：头部底图从 y=0 开始，与海报最顶部平齐，引擎强制 `bg_y_offset=0`
  - **底部渐变到透明铁律**（§10 更新）：底图底部渐变改为 alpha 0（全透明），让全局底图透出，不再叠背景色
  - **副标题间距铁律**（§14）：`tight_bottom` 始终跟随 `_wordart_bottom + 8px`，不截断，副标题与大标题视觉间距 ≤ 1cm
  - 新增 §13 完整生图规范（size/prompt 要求/存储路径/brief 字段一一对应）
  - `compose_long_poster()` 函数头注释固化四层架构和 AI 执行步骤

- **v0.10.3**（2026-05-29）：
  - 底图宽度铁律：`bg_image_fit` 引擎强制 `"width"`，底图始终铺满画布宽度，`bg_image_max_height` 不再截断高度；生图必须指定 `size="1440x900"`（或同宽）
  - 底图底部渐变铁律：渐变位置锚定底图实际底边，`bg_image_bottom_fade` 强制最小 80 不可设为 0，渐变高度 = 底图高度 × 35%，彻底消除底图与正文区硬切线
  - 艺术字生图铁律：必须纯黑底（`#000000`）生图 + `chroma_key=true` 抠底，禁止直接用透明底生图（不稳定）
  - 副标题装饰框铁律：`render_subtitle_text` 默认 `frame_style="none"`，禁止 diamond 等装饰框样式

- **v0.10.2**（2026-05-28）：
  - 新增 `table_module` 组件（HTML→Playwright 截图，支持大圆角卡片、CSS渐变等美观效果）
  - `table_module` 支持 `theme_overrides` 字段，可精确注入海报主色，实现配色跟随
  - SKILL.md 固化触发规则：用户明确声明「复杂表格图形」才用 `table_module`，否则默认 `complex_table`

- **v0.10.1**（2026-05-27）：
  - 画布宽度从 1200px 扩展到 1440px（支持7列以上复杂表格）
  - 新增 `complex_table` 组件（支持 rowspan/colspan 合并单元格、竖线/横线分段跳过、列宽权重+下限）
  - 新增 `subtitle_text` 组件（游戏风格艺术字：外发光 + 主体文字 + 轮廓描边，颜色跟配色方案）
  - `top_logo_bar` 新增 `logo_heights` 数组（支持每个 logo 单独指定高度，解决宽高比差异大时视觉不均匀问题）
  - `hero_strip` 中 `logo_slot` 默认值改为 `None`（不再自动渲染品牌 logo，避免与 top_logo_bar 重复）
  - `compose_poster_v2.py` 中 `logo_reserved_top` 改为从 `top_logo_bar` section 读取实际参数（精确下移背景图）
  - **固化铁律**：顶部 logo 横幅（不重复、不用 footer）、复杂表格框线、正文框不溢出为通用铁律；配色、样式、字色为场景灵活项
  - 修复 `wrap_cjk` 行尾禁排字符（`TAIL_FORBIDDEN`）在极窄列的无限循环 bug
- **v0.10**（2026-05-20）：assets/uploads/ 规范 + data_table 通用表格组件 + content.md→brief 转换器 + 零占位铁律全面落实
- **v0.9**：模块化主线（10 模块编号 + 12 套命名配色 + measure-first 全部组件）
- **v0.8**：AI 艺术字 PNG 双 provider + chroma-key 抠图 + recolor 重染
- **v0.7**：12 套配色预设 + 5 新组件（curriculum_timeline / faculty_grid / benefit_grid / notice_box / contact_text）
