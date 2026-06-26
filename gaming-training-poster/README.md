# Gaming Training Poster — Skill 包

游戏大厂人才发展场景下的培训海报生成 Skill。  
**核心架构**：AI（Nano Banana / Image2）出主视觉底图 + PIL 精准合成中文标题 / Logo / 信息层。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API
export IMAGE_PROVIDER=nano_banana
export NANO_BANANA_API_KEY=sk-xxx
export NANO_BANANA_BASE_URL=https://api.nanobanana.example.com/v2

# 3. 准备 brief（参考 scripts/example_brief.json）
# 4. 跑两阶段
python scripts/gen_background.py --brief scripts/example_brief.json --out output/
python scripts/compose_poster.py --bg output/<timestamp>_bg_1.png \
    --brief scripts/example_brief.json --out output/final.png
python scripts/qa_check.py --img output/final.png
```

## 目录速查

| 路径 | 作用 |
|---|---|
| `SKILL.md` | 主流程：何时使用、6 大场景路由、五步工作流、反模式 |
| `references/brand-guide.md` | 品牌调性、燃度尺、红线、一致性清单 |
| `references/design-system.md` | 色板 / 字阶 / 栅格 / 间距 / 装饰组件库 |
| `references/scene-prompts.md` | S1-S6 各自的 base prompt + negative |
| `references/nano-banana-api.md` | 图像 API 封装规范 |
| `scripts/gen_background.py` | Stage 1：调 API 出底图 |
| `scripts/compose_poster.py` | Stage 2：PIL 精准合成 |
| `scripts/qa_check.py` | 量化自检（对比度、尺寸、文件大小） |
| `scripts/lib/` | prompt_builder / layout / palette 三个共享模块 |
| `assets/` | 用户需提供的 Logo / 字体 / 图标 / 纹理 / 样图 |

## 用户需补充的素材

- `assets/logos/`：主 / 亮 / 暗 三版 Logo
- `assets/fonts/`：中文 Heavy + 装饰字体（兼容 `font_gaming_bold.ttf` 这一默认引用）
- `references/design-system.md` 中的 `#TBD` 替换为真实品牌色

## 设计原则（一句话）

> 中文 / Logo / 关键信息绝不交给 AI 去画。AI 只负责氛围，PIL 负责精度。
