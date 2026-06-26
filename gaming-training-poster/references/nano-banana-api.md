# Nano Banana 2 / Image2 API 使用说明

> 本 Skill 兼容 Nano Banana 与 Image2 两套 API，通过 `IMAGE_PROVIDER` 环境变量切换。
> 实际 endpoint / 鉴权方式以厂商最新文档为准；本说明聚焦"本 Skill 怎么用"。

## 1. 环境变量

```bash
export IMAGE_PROVIDER="nano_banana"   # 或 "image2"
export NANO_BANANA_API_KEY="sk-xxx"
export NANO_BANANA_BASE_URL="https://api.nanobanana.example.com/v2"
export IMAGE2_API_KEY="sk-yyy"
export IMAGE2_BASE_URL="https://api.image2.example.com/v1"
```

## 2. 统一调用接口（封装在 scripts/lib/prompt_builder.py）

```python
from scripts.lib.prompt_builder import generate_image

img_path = generate_image(
    prompt="...",                    # Stage 1 拼装好的英文 prompt
    negative_prompt="...",
    width=1024,
    height=1536,                     # A3 竖版比例 ≈ 2:3
    steps=40,
    guidance_scale=7.5,
    seed=None,                       # 复现时固定
    n=4,                             # 一次出 4 张候选
    out_dir="output/",
)
```

## 3. 推荐参数（按场景）

| 场景 | guidance_scale | steps | 说明 |
|---|---|---|---|
| S1 / S4 | 7.0 | 35 | 朝气/温暖，参数偏温和 |
| S2 / S5 | 8.0 | 45 | 仪式/沉稳，需要更精细的细节 |
| S3 / S6 | 7.5 | 40 | 极客/对抗，平衡 |

## 4. 错误处理

| 错误码 | 含义 | 处理 |
|---|---|---|
| 429 | 限流 | 指数退避，最多 3 次 |
| 400 NSFW | 触发安全过滤 | 检查 prompt 中是否含暴力/敏感词，剔除后重试 |
| 5xx | 服务端 | 退避后切到备用 provider |
| timeout | 超时 | 单图超 60s 视为失败，重发 |

## 5. 成本与配额

- 单张海报项目预算：≤ 8 次 API 调用（4 候选 + 最多 2 轮重抽 + 2 张备用尺寸）
- 超过预算时停手，向用户汇报并请求确认

## 6. 不要做的事

- ❌ 把品牌色十六进制丢进 prompt（模型不认）→ 用语义色描述（"deep navy with golden constellation"）
- ❌ 把中文标题放进 prompt → 文字必然糊
- ❌ 在 prompt 里说 "logo of XX company" → 必然变形，Logo 走 PIL
- ❌ 让 API 出 PNG 透明底 → 不稳定，统一出不透明 PNG，需要透明背景时本地抠图

## 7. 提示工程版本管理

每次成功的 prompt → 写入 `output/{timestamp}_meta.json`，记录：
- 完整 prompt
- 参数
- 用户 brief
- 用户最终选择的版本号

便于 A/B 复盘与未来微调。
