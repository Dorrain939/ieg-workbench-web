# Assets 资产说明

> 本目录内的素材文件需要由用户提供。当前为占位说明，列出每个文件的命名约定与用途。

## logos/
品牌主 Logo 系列。**至少需要 3 个版本**：

| 文件名 | 用途 |
|---|---|
| `logo_gaming_main.png` | 默认主 Logo（彩色，适合中性底） |
| `logo_gaming_light.png` | 亮色版本（适合深色底） |
| `logo_gaming_dark.png` | 深色版本（适合浅色底） |
| `logo_training_center.png` | 培训中心子标识（可选） |

**要求：** PNG 透明底，长边 ≥ 1024px，无外部留白。

## icons/
游戏化通用图标系统。建议至少包含：

- `icon_level_up.png` 等级提升
- `icon_badge.png` 勋章
- `icon_rocket.png` 启航
- `icon_trophy.png` 奖杯
- `icon_code.png` 代码
- `icon_team.png` 团队
- `icon_qr_frame.png` 二维码外框

**要求：** PNG 透明底，统一线宽与圆角，128×128 或 256×256。

## fonts/
字体文件。**至少需要：**

| 文件名 | 用途 |
|---|---|
| `font_cn_heavy.otf` | 中文标题（推荐：思源黑体 Heavy） |
| `font_cn_regular.otf` | 中文正文（思源黑体 Regular） |
| `font_en_display.ttf` | 英文/数字标题（Druk Wide / Bebas Neue） |
| `font_gaming_bold.ttf` | 游戏风装饰字体（兼容 compose_poster.py 中的默认引用） |

**要求：** 商业授权清晰；CJK 字体需确保字符全集覆盖。

## textures/
场景纹理底图。每个场景至少 1 张：

- `texture_pixel_burst.png` 像素飞溅
- `texture_circuit.png` 电路纹理
- `texture_starfield.png` 星空
- `texture_velvet.png` 天鹅绒（仪式感）
- `texture_scoreboard.png` 计分板条带

**要求：** PNG，可选透明底，1024×1024 或更大。

## samples/
每个场景 1-2 张参考样图，用于风格锚定与未来 LoRA / Reference Image 训练。

```
samples/
├── S1_onboarding_ref.jpg
├── S2_leadership_ref.jpg
├── S3_tech_ref.jpg
├── S4_culture_ref.jpg
├── S5_promotion_ref.jpg
└── S6_hackathon_ref.jpg
```
