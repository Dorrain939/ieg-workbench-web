# 零 API 快速上手 · 5 步出第一张海报

> 不需要任何 API key，不需要付费账号，今天就能跑通。
> 整个流程：**网页端出底图 → 写 brief → 跑合成脚本 → 拿到成品 PNG + PDF**

---

## 准备清单（一次性，5 分钟）

### 1. 中文字体（必需）
PIL 默认字体不支持中文，必须放一个中文字体到 `assets/fonts/font_gaming_bold.ttf`。

**最快方案（仅供测试出图）**：
```bash
# macOS 自带的冬青黑体简体中文，可用于测试
cp "/System/Library/Fonts/Hiragino Sans GB.ttc" \
   ~/.workbuddy/skills/gaming-training-poster/assets/fonts/font_gaming_bold.ttf
```
> ⚠️ **正式商用前必须替换为有授权的字体**。Hiragino 属于商业字体，仅 macOS 系统使用授权。
>
> 推荐免费商用方案：
> - **阿里巴巴普惠体**（https://fonts.alibabagroup.com/） — 阿里出品，免费商用
> - **思源黑体 Heavy**（Adobe + Google 开源） — 字重选择多
> - **字魂免费字商用专区**（https://izihun.com/） — 游戏感更强的装饰字体在这里找

### 2. Logo（可选，无 Logo 流程也能跑）
放一个 PNG（建议透明底）到：
```
assets/logos/logo_gaming_main.png
```
没有的话脚本会自动跳过并打印 warning。

### 3. Python 依赖
```bash
cd ~/.workbuddy/skills/gaming-training-poster
pip install -r requirements.txt
```

---

## 五步走

### Step 1 · 选场景，复制 prompt
打开 `references/web-prompts-cn.md`，找到你这次要做的场景（S1-S6），复制对应 prompt。

### Step 2 · 网页端出底图
推荐用**豆包/即梦**或**通义万相**：
- 粘贴 prompt
- 比例选 **3:4** 或 **9:16**（竖版海报）
- 出 4-6 张候选，挑一张顶部和底部留白最干净的
- 下载，重命名为 `bg_v1.png`，放到 `assets/samples/` 下

### Step 3 · 写 brief
新建 `output/my_brief.json`：
```json
{
  "scene": "S1",
  "title": "2026 新人启程营",
  "subtitle": "Welcome Aboard, Player One",
  "date": "2026.06.10 - 06.14",
  "location": "总部 · 大学堂 A",
  "host": "人才发展中心",
  "key_points": [
    "破冰团建",
    "业务全景课",
    "导师 1v1",
    "项目初体验"
  ],
  "qr_code": null
}
```
> 字段都可选，留空就不渲染。

### Step 4 · 跑合成
```bash
cd ~/.workbuddy/skills/gaming-training-poster
python scripts/compose_poster.py \
  --bg assets/samples/bg_v1.png \
  --brief output/my_brief.json \
  --out output/poster_v1.png
```
30 秒内出图。同时生成 PDF（300dpi 印刷友好）。

### Step 5 · QA 自检
```bash
python scripts/qa_check.py --image output/poster_v1.png
```
检查对比度、尺寸、文件大小。不过关则换底图或调 brief 重跑。

---

## 常见问题

**Q: 出图时网页 AI 还是塞了字进去怎么办？**
A: prompt 末尾再追加 `严禁出现任何文字 字母 汉字 数字 watermark`，或换张候选图。最差情况——用 PS 把文字区涂掉再喂给脚本。

**Q: 标题撞到底图主体了？**
A: 你换一张顶部更干净的候选图。或者编辑 `compose_poster.py` 里 `_draw_title_block` 的 `title_y` 参数（默认 0.38，调到 0.45 会下移）。

**Q: 字号太大/太小？**
A: 默认按 A3 尺寸（h=3508）的 200pt 主标题。出图尺寸不一样脚本会自动按比例缩放。如果你的标题字数特别多（>10 字），建议拆成主标题 6 字以内 + 副标题。

**Q: 想要不同纵横比（朋友圈 1:1、公众号横版）？**
A: 网页端出对应比例的图即可，脚本会按底图比例适配。

---

## 流程一旦跑通后

跑完 3-5 张真实海报你会有手感，到时再看：
- 网页端出图够不够稳定？流量大了要不要上 API？
- 字号、留白、Logo 位置要不要微调？（改 `compose_poster.py` 即可）
- 哪些场景最常用？（用得多的场景才值得继续优化 prompt）

**反原则**：在跑通真实场景前，不要把时间花在调 API 接入、调字号 0.5pt 这种细节上。
