# Design System · 设计系统规范

> 这份文件解决"复杂元素堆砌下风格仍然统一"的核心痛点。所有合成阶段（Stage 2）必须严格遵守。

## 1. 色板（Color Tokens）

> 占位色值，请用户提供品牌色后替换为真实值。每个场景有 1 个 Primary、2 个 Accent、1 个 Neutral。

### 全局
```yaml
brand_primary:    "#TBD"   # 公司品牌主色（待用户提供）
brand_secondary:  "#TBD"   # 公司品牌辅色
ink_900:          "#0E0F1A"  # 深黑（标题字）
ink_500:          "#5C5E73"  # 中灰（正文字）
ink_100:          "#F4F5FB"  # 浅底
white:            "#FFFFFF"
```

### 场景调色（占位，需要用户最终确认）
```yaml
S1_onboarding:    { primary: "#3B82F6", accent_a: "#FBBF24", accent_b: "#10B981", neutral: "#0F172A" }   # 朝气蓝 + 像素金
S2_leadership:    { primary: "#1E1B4B", accent_a: "#C9A961", accent_b: "#475569", neutral: "#0B1020" }   # 深空蓝 + 勋章金
S3_tech:          { primary: "#0F172A", accent_a: "#22D3EE", accent_b: "#A78BFA", neutral: "#020617" }   # 极客深 + 霓虹青/紫
S4_culture:       { primary: "#F97316", accent_a: "#EC4899", accent_b: "#FACC15", neutral: "#FFF7ED" }   # 节日橙 + 烟花粉
S5_promotion:     { primary: "#7C2D12", accent_a: "#FBBF24", accent_b: "#FFFFFF", neutral: "#1C1917" }   # 仪式酒红 + 金
S6_hackathon:     { primary: "#DC2626", accent_a: "#16A34A", accent_b: "#FACC15", neutral: "#0A0A0A" }   # 电竞红 + 信号绿
```

**规则：**
- Primary 占画面 30-50%
- Accent A/B 共占 15-25%
- Neutral 兜底（背景或留白）
- 任何场景都不超过 4 个主要颜色

## 2. 字阶（Type Scale）

A3 竖版（2480×3508 @ 300dpi）尺寸下：

| 角色 | 字号(pt) | 字重 | 字体（中/英） | 行距 |
|---|---|---|---|---|
| Display 主标题 | 180-220 | Heavy / 900 | 思源黑体 Heavy / Druk Wide | 1.05 |
| H1 副标题 | 96-120 | Bold / 700 | 思源黑体 Bold / Inter Bold | 1.15 |
| H2 段落标题 | 56-72 | SemiBold / 600 | 思源黑体 Medium | 1.3 |
| Body 正文 | 36-44 | Regular | 思源黑体 Regular / Inter | 1.5 |
| Meta 信息 | 28-36 | Medium | 思源黑体 Medium / Inter Medium | 1.4 |
| Stamp 装饰 | 24-32 | Bold + 字距加宽 | 数字与英文用 Druk / Bebas | — |

**A4/公众号头图按比例缩放，但层级关系保持不变。**

## 3. 栅格（Grid）

```
┌──────────────────────────┐
│        Margin 8%          │
│  ┌────────────────────┐   │
│  │  HEADER  35%       │   │  ← Logo + 项目识别
│  ├────────────────────┤   │
│  │  HERO    40%       │   │  ← 主视觉 + 标题
│  ├────────────────────┤   │
│  │  INFO    25%       │   │  ← 信息 + 二维码
│  └────────────────────┘   │
│        Margin 8%          │
└──────────────────────────┘

水平 12 栅格，槽间距 = 24pt（A3）
```

**安全边距：**画布外缘 8% 是禁飞区，重要信息不进入。

## 4. 装饰组件库（Decorations）

每个场景准备一套"零件"，组合而非新画：

| 组件 | 形态 | 用法 |
|---|---|---|
| `pixel_burst` | 像素粒飞溅 | 标题角落、Hero 边缘 |
| `level_bar` | 等级进度条 | Header 副标识 |
| `badge_circle` | 勋章圆章 | 表彰场景必出 |
| `code_rain` | 代码雨纹理 | 技术场景背景 |
| `glow_line` | 霓虹分割线 | 信息区分隔 |
| `corner_bracket` | L 形装饰角 | 强调 Hero 区 |
| `qr_frame` | 二维码外框 | 二维码必加框防止融底 |

存放在 `assets/textures/` 与 `assets/icons/`。

## 5. 间距系统（Spacing Tokens）

8pt 基准：`xs=8, sm=16, md=24, lg=40, xl=64, xxl=96`（A3 下乘 2）

文字与图形最小净距 = `md`，文字与画布边 = `lg`。

## 6. 对比度规则

- 文字 vs 背景：WCAG AA 4.5:1（正文）/ 3:1（≥24pt 标题）
- 任何文字落在 AI 底图上时，**底层必须铺一层渐变遮罩**：
  - 顶部文字区：`linear-gradient(180deg, neutral_900_60% → transparent)`
  - 底部信息区：`linear-gradient(0deg, neutral_900_70% → transparent)`

## 7. 一致性"防崩塌"三条铁律

1. **同一张海报，最多 3 个字体族**（中文 1 + 英文/数字 1 + 装饰 1）
2. **同一张海报，色板严格来自当前场景的 4 色**，不混入其他场景的色
3. **装饰组件最多用 5 个**，且必须来自同一风格族（像素族 / 霓虹族 / 仪式族不混用）
