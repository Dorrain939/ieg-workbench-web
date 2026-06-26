# v0.7 HTML/CSS + Playwright 重构方案

> 起草于 v0.6 完成节点（chip+panel 改造、AI 底图通路打通）。
> 当前 PIL 路径已经突破 1800 行手写绘制代码，进入边际收益递减区——再往「报纸级别」的复杂排版走，应该换轨。

---

## 一、为什么要换轨

### 1. PIL 路径目前的硬伤

| 维度 | 现状 | 痛点 |
|---|---|---|
| 中文换行 | 手写 `wrap_cjk` token 化（v0.6 已上） | 还差「英文连字符断词、中英混排紧排、引号配对」等细节，每条规则都要手写 |
| 字体效果 | stroke / shadow / gradient 自己叠通道 | 没有 letter-spacing、没有 text-decoration、ligature 不可控 |
| 多列 / Flex | 手算 anchor 与 bbox | 多人头像横排、`info_card_with_qr` 左文右二维码这类「小 Flex」全靠 ctx.x_offset 拼 |
| 表格 | `schedule_table` 手写每行 y、列宽 | 一旦多列、合并单元格、跨行高亮就崩 |
| 装饰避让 | `PlacementMap` 30 次重试 + 禁飞区 bbox | 装饰一密就退化为「能放几个放几个」（v0.6 出图实测 7/8） |
| 光影 | drop_shadow / inner_highlight 都是像素级算 | 同样的 box-shadow 在 CSS 一行写完 |
| 改版迭代 | 改一处样式要重跑 30s+ 出图 | 反馈环慢，难以做风格批量 A/B |

### 2. HTML/CSS 渲染的硬优势

- **CSS 排版引擎是工业级的**：CJK 行首/行尾禁排、word-break、hanging-punctuation、letter-spacing、leading-trim 都是浏览器免费送的。
- **Flex / Grid / Subgrid**：13 个组件的内部排布直接退化为 `display:flex` / `grid-template`。
- **变量化与主题切换**：把 6 套 scene × 12 套 scheme 全做成 `:root { --primary: #...; }`，切换只改 className。
- **filter / backdrop-filter / mask / clip-path**：磨砂玻璃、贴图剪裁、形状蒙版直接 CSS 化。
- **Web Font + variable font**：可变字重、刻字假名、伪斜体等。
- **可调试**：任何一张图都可以用 Chrome DevTools 直接调样式，所见即所得。
- **截图速度**：Playwright 调一次 1200×4500 截屏 ≈ 1-2s（含字体加载与 layout），比 PIL 全像素绘制快一个量级。

### 3. 需要保留的 PIL 资产

- `palette_lab.py`：12 套配色方案 + best_text_color。可以直接生成 CSS 变量。
- `copy_writer.py`：6 场景文案模板 + AUTO 占位。HTML 路径仍由 Python 端生成最终 brief。
- `decorations.py` 资产清单：装饰 PNG 库直接 `<img>` 引入。
- `assets.py` 的 logo/字体 slot 解析：在 HTML 路径下变成 `<link>` / `<img>` 注入。
- AI 底图通路（`buddy-cloud.py image` + 缓存到 `assets/samples/`）：完全复用，HTML 里走 `background-image: url(...)`。

---

## 二、目标架构

```
Brief (JSON) ─┐
              ├─► Python: render_html.py
Palette ──────┤    - 选 scheme → CSS 变量
Copy Writer ──┤    - auto_fill → 文案补齐
AI 底图路径 ───┘    - Jinja2 渲染 long_poster.html
                          │
                          ▼
              dist/poster.html  +  dist/poster.css
                          │
                          ▼
              Playwright (chromium headless)
                          │
                          ▼
              poster.png  /  poster.pdf
```

### 关键文件

| 文件 | 职责 |
|---|---|
| `scripts/render_html.py` | 取代 `compose_poster_v2.py` 主入口；生成 dist 后调 Playwright |
| `scripts/lib/jinja_env.py` | Jinja2 环境配置 + 自定义 filter（颜色、QR、长度截断） |
| `templates/long_poster.html.j2` | 长图主模板 |
| `templates/sections/*.j2` | 13 个 section 子模板：hero_strip / lead_paragraph / info_card / info_card_with_qr / qa_block / meta_row / schedule_table / resource_grid / cta_button / rules_box / contact_card / section_title_bar / footer_logobar |
| `templates/css/base.css` | reset + 字体 + canvas 框 |
| `templates/css/components.css` | 13 组件样式 |
| `templates/css/themes.css` | 12 配色方案对应的 :root 选择器（按 `data-scheme="S1-aurora"` 切换） |
| `templates/css/decorations.css` | 散点装饰 keyframe + 位置生成器 |
| `scripts/lib/playwright_shoot.py` | 装载 HTML，截整页 PNG / 打印 PDF |

---

## 三、Brief Schema 兼容策略

**目标：v2 brief 直接喂进 v0.7，不改字段。**

- `scene` / `scheme_id` / `vibe`：保留 → 在模板里输出 `<body data-scene="S1" data-scheme="S1-aurora">`
- `canvas.bg_image_path`：保留 → CSS `background-image: url('file://...')`
- `canvas.glow / glow_top_color / glow_bottom_color`：保留 → 两个绝对定位的径向渐变 div
- `canvas.pattern: "grid"|"dots"`：保留 → CSS background 多层叠加
- `canvas.grain: true`：保留 → 一个 SVG noise 滤镜或 PNG 贴图
- `decoration_family / decorations`：保留 → 模板里取 `assets/icons/decoration_pack_<family>/` 下随机抽 N 张 → 用 absolute positioning 加 z-index 撒点
- `sections[*]`：每个 section 由对应 `templates/sections/<type>.j2` 子模板渲染

新增字段（HTML 特有，向下兼容）：

- `canvas.css_extra` *(可选)*：原始追加 CSS（运营手动微调时用）
- `canvas.font_face` *(可选)*：本地字体文件路径数组，注入 `@font-face`
- 每个 section 可加 `class_extra` 字段，便于运营手贴一些 utility class

---

## 四、组件 → CSS 翻译速查

### hero_strip

```html
<section class="hero">
  <div class="hero-screen">
    {% if logo_slot %}<img class="hero-logo" src="{{ logo_path }}">{% endif %}
    <h1 class="hero-title gradient-large">
      {% for line in title_card.lines %}<span>{{ line }}</span>{% endfor %}
    </h1>
  </div>
</section>
```

```css
.hero-screen{
  height: 720px;
  display:flex; flex-direction:column; justify-content:flex-end; gap:24px;
  padding: 56px;
  background: radial-gradient(ellipse at top, var(--glow-top) 0%, transparent 60%),
              linear-gradient(180deg, var(--bg-0), var(--bg-1));
}
.hero-title{
  font-family: var(--font-display);
  font-size: 130px; line-height: 1.05; font-weight: 900;
  background: linear-gradient(180deg, var(--title-a), var(--title-b));
  -webkit-background-clip: text; color: transparent;
  filter: drop-shadow(0 6px 18px rgba(0,0,0,.45));
}
```

### info_card_with_qr（v0.6 PIL 里 200 行 → CSS 12 行）

```css
.info-card-qr{
  display:grid; grid-template-columns: 1fr 220px; gap:32px;
  background: var(--panel-dark) / .9;
  border: 2px solid var(--accent-a);
  border-radius: 24px; padding: 36px;
}
```

### qa_block 单条

```css
.qa-item{
  background: var(--panel-dark);
  border-left: 4px solid var(--accent-a);
  border-radius: 16px; padding: 20px 24px;
}
.qa-item .q{ color: var(--accent-a); font-weight:700; margin-bottom:8px; }
.qa-item .a{ color: var(--text-on-dark); line-height:1.7; }
```

### 散点装饰

```css
.deco{
  position:absolute; pointer-events:none;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,.3));
}
.deco--rotate-left { transform: rotate(-12deg); }
```

放置：Python 端在生成模板上下文时跑一次 PlacementMap（复用现有逻辑），输出 `[{img, top, left, rotate, w}]` 列表，模板里 for 循环输出 `<img class="deco" style="top:{{px}}px;left:...">`。

---

## 五、Playwright 截图脚本骨架

```python
# scripts/lib/playwright_shoot.py
from playwright.sync_api import sync_playwright

def shoot(html_path: str, png_path: str, pdf_path: str | None = None,
          width: int = 1200, scale: float = 2.0):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": width, "height": 100},
            device_scale_factor=scale,
        )
        page = ctx.new_page()
        page.goto(f"file://{html_path}")
        # 等字体与背景图加载
        page.evaluate("document.fonts.ready")
        page.wait_for_load_state("networkidle")
        # 全页截图
        page.screenshot(path=png_path, full_page=True, type="png")
        if pdf_path:
            page.pdf(path=pdf_path, width=f"{width}px",
                     print_background=True, prefer_css_page_size=True)
        browser.close()
```

依赖：`pip install playwright && playwright install chromium`（首次安装包 ≈ 200MB）。

---

## 六、迁移路线（建议两个 sprint）

### Sprint 1（≈ 5 天）：单场景 IF 调查问卷端到端

1. day 1：搭骨架 `templates/long_poster.html.j2` + base.css + 字体加载，render_html.py 跑通空页截屏
2. day 2：实现 hero_strip / lead_paragraph / info_card / info_card_with_qr 四组件 + S1-aurora 主题
3. day 3：qa_block / contact_card / footer_logobar，对齐 v0.6 视觉
4. day 4：装饰层 + AI 底图 + grain，与 v0.6 同 brief 对比
5. day 5：四联对比图（v0.5 / v0.6 / v0.6+AI / v0.7-html），写 README，删 PIL 长图主链路标记 deprecated

### Sprint 2（≈ 5 天）：剩余 5 场景 + 12 套主题 + 可调试模式

1. day 1-2：把 12 套 ColorScheme 翻译成 themes.css；scene S2-S6 各画一张参考样图
2. day 3：补齐 schedule_table / resource_grid / meta_row / cta_button / rules_box
3. day 4：装饰族 pixel-y2k vs semi-3d-collage 的 CSS 双方言
4. day 5：开 `--debug` 模式，截图前不关浏览器，输出 dist/index.html 让运营直接 Chrome 打开调样式

---

## 七、风险与对冲

| 风险 | 影响 | 对冲 |
|---|---|---|
| Playwright 首次安装 200MB | 用户感知较重 | 在 SKILL.md 写明，启动时检测并提示一行命令；保留 PIL 路径作为「无 Playwright fallback」 |
| 字体在 headless chromium 加载乱码 | 中文 fallback | 强制 `@font-face` 指向本地 ttf，并在 page.evaluate('document.fonts.ready') 后再截图 |
| filter / backdrop-filter 在 chromium pdf 模式不渲染 | PDF 比 PNG 丑 | PDF 用 `print_background=true` + 关闭部分 filter；或者直接 PNG → 转 PDF（PIL 一行） |
| AI 底图体积大导致截屏慢 | 单图 5s+ | 模板里把 bg-image 缩到 1200 宽再用；或者 Python 端预压缩 |
| 散点装饰位置浏览器与 PIL 不一致 | 复用 PlacementMap 在 viewport 像素空间里跑一次即可，再吐 absolute 坐标 | 同左 |
| 运营改 CSS 改坏了 | 截图静默失败 | render_html.py 加 `--lint` 模式，在 dist/ 跑 stylelint + 一些 tag 完整性检测 |

---

## 八、与 PIL 路径的去留

- **保留**：`palette_lab.py`、`copy_writer.py`、`assets.py`、AI 底图缓存层、装饰资产库。
- **冻结**：`compose_poster_v2.py` / `components.py` / `effects.py` / `text_layout.py`（标记 `@deprecated`，留作 fallback 与单元测试参照）。
- **删除时机**：v0.7 完整覆盖 6 场景 × 12 主题 × 真实数据三轮以后，再决定是否物理删除。

---

## 九、决策点（需要业务侧确认再启动）

1. **是否接受额外依赖 Playwright + Jinja2**？（200MB chromium）
2. **运营是否需要「在浏览器里直接调最终海报样式」的能力**？如需要，v0.7 价值翻倍。
3. **PDF 输出是否仍是硬指标**？如是，则需要在 Sprint 1 day 4 做 PDF 专项验证。
4. **是否要保留 PIL 路径作为 zero-dependency fallback**？建议保留 6 个月。

— 文档止 —
