"""
拼三联对比图：v0.5（无 AI 底图）/ v0.6（chip+panel 改造）/ v0.6+AI（接入 aurora 底图）
- 等宽缩略到 480 宽，并排
- 顶部贴版本徽章
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.expanduser("~/.workbuddy/skills/gaming-training-poster")
SRC = {
    "v0.5 baseline":     os.path.join(ROOT, "output/v2_if_survey_v05.png"),
    "v0.6 chip+panel":   os.path.join(ROOT, "output/v2_if_survey_v06.png"),
    "v0.6 + AI 底图":     os.path.join(ROOT, "output/v2_if_survey_v06_with_ai.png"),
}
OUT = os.path.join(ROOT, "output/compare_v05_v06_v06ai.png")

THUMB_W = 520
GAP = 24
HEADER_H = 88
PAD = 32

# 取第一张算高度
imgs = {}
target_h = 0
for k, p in SRC.items():
    im = Image.open(p).convert("RGB")
    ratio = THUMB_W / im.width
    new_h = int(im.height * ratio)
    im = im.resize((THUMB_W, new_h), Image.LANCZOS)
    imgs[k] = im
    target_h = max(target_h, new_h)

# 统一画布
total_w = PAD * 2 + THUMB_W * 3 + GAP * 2
total_h = PAD * 2 + HEADER_H + target_h + 60

canvas = Image.new("RGB", (total_w, total_h), (16, 18, 32))
draw = ImageDraw.Draw(canvas)

# 字体
font_path_zh = "/System/Library/Fonts/Hiragino Sans GB.ttc"
font_path_en = "/System/Library/Fonts/SFNS.ttf"
try:
    f_title = ImageFont.truetype(font_path_zh, 36)
    f_sub   = ImageFont.truetype(font_path_zh, 18)
    f_label = ImageFont.truetype(font_path_zh, 22)
except Exception:
    f_title = ImageFont.load_default()
    f_sub   = ImageFont.load_default()
    f_label = ImageFont.load_default()

# 顶标
draw.text((PAD, 18), "IF 调查问卷长图 · v0.5 → v0.6 → v0.6+AI 三联对比",
          fill=(240, 240, 240), font=f_title)
draw.text((PAD, 64), "排版换行修复 / 全去 stroke 描边 / chip+panel 衬底 / AI 极光底图",
          fill=(160, 168, 200), font=f_sub)

# 版本横幅颜色
banner_colors = {
    "v0.5 baseline":   (123, 87, 230),
    "v0.6 chip+panel": (251, 191, 36),
    "v0.6 + AI 底图":   (16, 185, 129),
}

# 排列三张
y0 = PAD + HEADER_H
for i, (k, im) in enumerate(imgs.items()):
    x = PAD + i * (THUMB_W + GAP)
    canvas.paste(im, (x, y0))

    # 在缩略图顶部叠版本胶囊
    bar_h = 38
    bar_y = y0 + 8
    bar_pad = 14
    text_w = draw.textlength(k, font=f_label)
    pill_w = int(text_w + bar_pad * 2)
    pill_x = x + 10
    pill = Image.new("RGBA", (pill_w, bar_h), banner_colors[k] + (255,))
    canvas.paste(pill, (pill_x, bar_y), pill)
    draw.text((pill_x + bar_pad, bar_y + 6), k, fill=(20, 20, 20), font=f_label)

# 底部尺寸说明
ftr_y = y0 + target_h + 18
draw.text((PAD, ftr_y),
          f"宽 1200 同源；缩略各 {THUMB_W}px；总尺寸 {total_w}×{total_h}",
          fill=(120, 130, 160), font=f_sub)

canvas.save(OUT, optimize=True)
print(OUT)
