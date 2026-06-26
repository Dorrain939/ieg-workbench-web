# Scene Prompts · 六大场景 Prompt 模板

> 每个场景只调一个 base prompt 模板。新增场景时，复制下方区块结构即可。
> 占位符 `{topic}` 由 brief.title 注入；`{vibe_extras}` 由用户 extras 注入。

---

## S1 · 新人训练营 / Onboarding

**Base Prompt（英文，Nano Banana 对英文响应更稳）：**
```
A vertical training poster background for a gaming company onboarding bootcamp,
hero element: a stylized rocket-shaped game console launching from a pixel-art
landscape, surrounded by floating "level 1" markers and softly glowing experience
points, isometric perspective, sense of new journey and progression, warm dawn
sky transitioning to deep blue, rich pixel-art accents, clean professional layout,
top 35% sky area kept clean for title placement, bottom 25% kept as soft gradient
ground for information overlay, subject: {topic} mood, {vibe_extras},
high detail, 8k, cinematic lighting, art direction by AAA game studio.
```

**Negative：** `text, letters, chinese characters, logo, watermark, signature, ui buttons, faces with deformed features, low resolution, cluttered`

**色板锁定：** `S1_onboarding`

---

## S2 · 领导力 / 管理者发展

**Base Prompt：**
```
A vertical training poster background for a senior leadership development program,
hero element: a majestic constellation forming a leader's silhouette overlooking
a vast strategic map, deep navy starfield with golden constellation lines,
metallic medal motifs subtly embedded in the lower zone, sense of vision,
gravitas and long-term thinking, restrained gaming aesthetic with subtle
hexagonal grid texture, top 35% deep sky kept clean for title, bottom 25%
darker zone for crisp white-text overlay, subject: {topic} mood, {vibe_extras},
high detail, museum-grade composition, cinematic.
```

**Negative：** `text, letters, chinese characters, logo, childish, cartoonish, neon overload, lens flare, low resolution`

**色板锁定：** `S2_leadership`

---

## S3 · 技术分享 / Tech Talk

**Base Prompt：**
```
A vertical poster background for an internal tech talk at a gaming company,
hero element: an abstract glowing engine core with circuit traces radiating
outward, holographic data streams and code-rain texture in the periphery,
cyber-dark background with cyan and purple neon highlights, futuristic geek
aesthetic, sense of focus and frontier exploration, top 35% kept as clean
dark space for title, bottom 25% with subtle horizontal data-bar texture
for info overlay, subject: {topic} mood, {vibe_extras}, ultra detail,
cinematic, blade-runner-meets-game-engine vibe.
```

**Negative：** `text, letters, chinese characters, logo, watermark, anime characters, real human faces, photo-realistic people`

**色板锁定：** `S3_tech`

---

## S4 · 文化活动 / 团建

**Base Prompt：**
```
A vertical poster background for a gaming company culture festival,
hero element: a warm pixel-art carnival scene with floating balloons,
fireworks bursting into pixel particles, soft confetti rain, joyful
gathering vibe, top 35% kept as soft warm sky for title, bottom 25%
as gentle ground gradient for info, palette: festive orange, candy pink
and golden yellow, sense of warmth, togetherness and celebration,
subject: {topic} mood, {vibe_extras}, hand-crafted feel, cinematic warmth.
```

**Negative：** `text, letters, chinese characters, logo, gloomy, dark horror, scary, low quality, cluttered`

**色板锁定：** `S4_culture`

---

## S5 · 晋升 / 表彰发布

**Base Prompt：**
```
A vertical award-ceremony poster background for a gaming company quarterly
promotion announcement, hero element: a luxurious medal-shaped emblem with
laurel wreath details, soft spotlight beams from above, deep wine-red velvet
backdrop with subtle damask texture, golden particles floating, sense of
honor, ritual and restrained pride, top 35% kept as clean dark velvet for
title, bottom 25% darker zone for info overlay, subject: {topic} mood,
{vibe_extras}, museum lighting, cinematic.
```

**Negative：** `text, letters, chinese characters, logo, gaudy, kitsch, cartoonish, low resolution`

**色板锁定：** `S5_promotion`

---

## S6 · 内部赛事 / Hackathon

**Base Prompt：**
```
A vertical poster background for an internal hackathon at a gaming company,
hero element: an electrifying scoreboard with red-vs-green team energy
clashing in the center, sparks of code particles, esports stadium vibe,
high contrast lighting, sense of intense competition and creative breakthrough,
top 35% kept as dark void for title, bottom 25% as scoreboard-strip texture
for info, subject: {topic} mood, {vibe_extras}, ultra detail, cinematic,
arena-grade composition.
```

**Negative：** `text, letters, chinese characters, logo, blood, gore, violent imagery, low resolution`

**色板锁定：** `S6_hackathon`

---

## 通用追加片段（每次都拼到末尾）

```
--composition_constraints
Top 35% MUST remain visually quiet (low-frequency tones) to allow large title text to overlay.
Bottom 25% MUST remain low-saturation gradient for high readability of small info text.
NO text rendering anywhere in the image. Image will be combined with crisp text via post-processing.

--quality
8k resolution, ultra detail, sharp focus, balanced composition, professional poster grade.
```

## Prompt 调试守则

1. 一次只改 1 个变量（hero / palette / texture / mood）
2. 同一 brief 出 4 张候选，pick 1 进入 Stage 2，其余存档供复盘
3. 出图偏差时优先调 **negative** 而不是堆 positive
4. 中文关键词只用于 brief，绝不进 prompt
