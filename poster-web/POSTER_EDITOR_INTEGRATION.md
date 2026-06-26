# POSTER_EDITOR_INTEGRATION.md

> **富文本编辑器升级 · 集成与迁移指引**
> 创建时间：2026-06-25
> 适用项目：`poster-web/`
> 设计原则：所见即所得（视觉一致）· 无品牌兜底 · 槽位级独立编辑 · 能力限制做品牌纪律

---

## 0. 本次升级做了什么

把现有 `<textarea>` / `<input type="text">` 简单输入框，全面升级为**槽位级富文本编辑器**：

- **每个文字槽位 = 独立 Tiptap 实例 + 贴身浮动迷你工具栏**
- **两档预设能力**：
  - `text-rich`：字体 / 字号 / B / I / U / 字色 / 高亮
  - `text-rich+image`：上一档 + 行内图片（多图并排 / 自由拖拽 / 段落对齐）
- **所见即所得**：编辑器和海报共享字号/颜色/行距/字体观感（不强求容器 1:1）
- **数据通路**：前端 `editor.getHTML()` → 后端 `sanitize_payload_deep()` → 注入海报模板
- **后端只删危险，不动样式**

---

## 1. 本次改动清单（5 处）

| # | 文件 | 改动 | 风险 |
|---|---|---|---|
| 1 | `static/index.html` | 在 head 内追加 Tiptap importmap + 加载 `rich-editor.js`（ES module）| 低 |
| 2 | `static/rich-editor.js` | **新文件**：核心 Tiptap 组件（Vue 3 Options API）| 低 |
| 3 | `static/styles.css` | 末尾追加 `.rich-editor` 一整套样式 | 低 |
| 4 | `static/app.js` | `FieldForm` 模板加 `rich`/`rich-image` 两个 `v-else-if` + 注册 `RichEditor` 组件（保留 textarea 降级）| 极低（纯增量）|
| 5 | `projects_api.py` | `update_function_project()` 入口加一行 `sanitize_payload_deep(payload)` | 极低 |
| 6 | `sanitize.py` | **新文件**：bleach 白名单清洗 + deep walker | 独立模块 |
| 7 | `requirements.txt` | 加 `bleach>=6.1`、`tinycss2>=1.2` | 需安装 |

**未改动的事**：
- `app.js` 主架构（6085 行）几乎不动，只在 `FieldForm` 末尾局部加了两个分支和一个 `components` 字段
- 现有 `text` / `textarea` / `array` / `bullets` 等字段类型 **完全不变**
- 现有所有模块的 schema 定义不变
- 后端模块数据结构不变

---

## 2. 安装步骤

```bash
cd poster-web/
pip install bleach>=6.1 tinycss2>=1.2

# 重启后端
./stop.sh && ./start.sh
```

前端无需打包，刷新浏览器即可。**首次加载会从 esm.sh CDN 拉取 Tiptap（约 200KB）**，之后浏览器缓存。

---

## 3. 怎么把某个 M 模块的字段从 `textarea` 升级为富文本

**只需要改字段定义里的 `type`**，其它一切不动。

### Before（旧）
```js
{
  key: 'body',
  label: '正文',
  type: 'textarea',           // ← 改这里
  default: '',
}
```

### After（仅文字，无图片）
```js
{
  key: 'body_html',           // 推荐改 key 加 _html 后缀（让后端清洗自动识别）
  label: '正文',
  type: 'rich',               // ← text-rich 预设
  preset: 'text-rich',        // 可省略，默认就是 text-rich
  placeholder: '请输入正文…',
  default: '',
}
```

### After（文字 + 行内图片）
```js
{
  key: 'body_html',
  label: '正文',
  type: 'rich-image',         // ← text-rich+image 预设
  placeholder: '请输入正文…',
  default: '',
}
```

**就这么简单**。富文本组件会自动：
- 提供贴身浮动迷你工具栏
- 调用 `/api/upload` 接口上传图片（复用现有上传通路）
- 在槽位失焦时隐藏工具栏
- 写回 HTML 到 `module.data[key]`

### 命名约定（重要）

> 富文本字段 key **必须以 `_html` 结尾**。

这样后端 `sanitize_payload_deep()` 会自动识别并清洗，不需要逐字段声明。

---

## 4. 25 个 M 模块的迁移建议

按 `poster_module_registry.py` 对照：

| 模块 | 旧字段 | 改成 | 预设 |
|---|---|---|---|
| M1 纯文字 | `body: textarea` | `body_html: rich-image` | text-rich+image |
| M2 含高亮纯文字 | `body: textarea` | `body_html: rich-image` | text-rich+image |
| M3 父子文字 | `sections[].title: text` + `sections[].body: textarea` | `sections[].title_html: rich` + `sections[].body_html: rich-image` | 标题 text-rich / 正文 text-rich+image |
| M4 无底框文字 | `body: textarea` | `body_html: rich` | text-rich |
| M5 文字+表格 | `intro: textarea` | `intro_html: rich-image` | text-rich+image |
| M6 单图图文 | `text: textarea` | `text_html: rich-image` | text-rich+image |
| M7 图文父子 | `sections[].text: textarea` | `sections[].text_html: rich-image` | text-rich+image |
| M8 文字+单图 | `text: textarea` | `text_html: rich-image` | text-rich+image |
| M9 文字+多图 | `text: textarea` | `text_html: rich-image` | text-rich+image |
| M10 单人卡 | `name/title/bio: text/textarea` | `name_html/title_html: rich` + `bio_html: rich-image` | 姓名/职位 text-rich / bio text-rich+image |
| M11 多张单人卡 | `people[].name/title` | `people[].name_html/title_html: rich` | text-rich |
| M12 多人头像墙 | `people[].name` | `people[].name_html: rich` | text-rich |
| M13 多人头像墙父子 | `groups[].title` + `groups[].people[].name` | 对应改 `_html: rich` | text-rich |
| M14 纯文字名单 | `names[]: array` | 暂保留 array（短名单不必富文本）| - |
| M15 文字名单父子 | `groups[].title + groups[].names[]` | 标题改 `title_html: rich` | text-rich |
| M16 课程卡（左讲师右课程）| `lecturer.name/title/bio` + `course.title/desc` | 对应 `_html` | text-rich(+image) |
| M17 课程卡（上文下讲师）| 同上 | 同上 | 同上 |
| M18 多课程父子 | `courses[].lecturer + courses[].content` | 对应 `_html` | text-rich(+image) |
| M19 评分条 | `items[].name + score` | `items[].name_html: rich` | text-rich |
| M20/M21 纯图片 | 不动 | 不动 | - |
| M22/M23 按钮 | `label: text` | `label_html: rich` | text-rich |
| M24 联系方式 | `text: textarea` | `text_html: rich` | text-rich |
| M25 二维码 | `text: textarea` | `text_html: rich` | text-rich |

> **建议**：渐进迁移。先升级 M1/M3/M6 几个高频模块，验收 OK 再批量升级。

---

## 5. 数据迁移：旧字段 → 新字段

**老项目里 `module.data.body` 是纯文本，新结构期待 `body_html` 是 HTML**。两个处理方案：

### 方案 A（推荐）：双字段读取兼容
模块字段定义里同时保留：
```js
{ key: 'body', label: '正文（旧）', type: 'textarea', visible: false },
{ key: 'body_html', label: '正文', type: 'rich-image' },
```
并在 `body_html` 初始化时检查：如 `body_html` 为空且 `body` 非空，自动包成 `<p>${body}</p>` 显示。

### 方案 B：一次性迁移脚本
写 Python 脚本扫所有项目 JSON，把 `body` 字段值改写到 `body_html` 里（包 `<p>`）。

### 方案 C（最简单）：新建项目用新结构，老项目继续用旧字段
两套并存，前端按 `key` 存在与否选择渲染。

---

## 6. 已实现 / 未实现 / 已知限制

### ✅ 已实现
- Tiptap v2 内核 + ES module CDN 加载
- 字体下拉（6 个：腾讯体/思源黑体/苹方/微软雅黑/Arial/Times New Roman）
- 字号下拉（12 档预设）+ 手动输入任意字号
- B / I / U 与激活态
- 字色 / 高亮（带 swatch 弹出 + 清除按钮）
- 行内图片：上传、8 方向自由拖拽、Shift 等比例
- 段落级图片对齐（左/中/右）
- 浮动迷你工具栏（focus 显示、延迟 180ms blur 防误触）
- 后端 bleach 白名单清洗（XSS 防护 + 保留所有用户样式）
- `sanitize_payload_deep()` 自动识别 `*_html` 字段

### ⚠️ 已知边界
- **图片"只能在所在行内左右换位"** ——这条目前由 ProseMirror 的 inline 语义天然约束（图片只能在段落 inline 内拖动），但是否需要更友好的"段内拖拽 UI"还需观察实际使用
- **不支持文字环绕**（按需求确认禁用）
- **不限图片大小**——只在 >5MB 时 console.warn，不阻断
- **图片上传接口**：`POST /api/upload`（带 FormData：file + session_id）；如果你后端是别的路径，在 RichEditor 上传时用 `:upload-url` prop 覆盖

### ❌ 未做（不在本次需求里）
- 列表（• / 1.）
- 表格（不在槽位级编辑能力里）
- 链接
- 上下标 / 删除线
- 撤销/重做按钮（用 Ctrl/⌘+Z 即可，工具栏不重复）
- 清除格式按钮

---

## 7. 调试 Tips

### 7.1 富文本组件没出现，仍然是 textarea
**原因**：`window.RichEditor` 还没准备好就被 FieldForm 注册了（CDN 加载晚于 app.js）。

**排查**：浏览器控制台跑：
```js
window.RichEditor   // 应该是个对象
```
如果是 `undefined`，说明 `/static/rich-editor.js` 加载失败，看 Network 面板。

**临时方案**：FieldForm 已加 textarea 降级，不影响保存。刷新页面通常即可（CDN 已缓存）。

### 7.2 工具栏 click 触发 blur 后立刻消失
本组件已用 `@mousedown="keepFocus"` 阻止默认行为，按钮按下不会失焦。如果还有问题，检查是否你的 CSS 改了 `.re-btn` 的 `:hover` 状态。

### 7.3 后端清洗丢样式
**可能性 1**：用户用了 `position` / `float` / `transform`——这些被强制删，按设计预期。
**可能性 2**：bleach 没装。运行：
```bash
python -c "import bleach; print(bleach.__version__)"
```

### 7.4 图片上传失败
检查 `/api/upload` 接口是否能接收：
- FormData
- `file` 字段（文件本体）
- `session_id` 字段（字符串）

返回 JSON 需要包含 `url` / `path` / `file_url` 之一。

---

## 8. 重启验证清单

```bash
# 1. 装依赖
pip install bleach>=6.1 tinycss2>=1.2

# 2. 自测 sanitize
python sanitize.py
# 应该看到 8 个用例的 IN/OUT

# 3. 启动
./start.sh

# 4. 打开浏览器
# http://127.0.0.1:8766/
```

### 验证项
- [ ] 控制台无报错
- [ ] `window.RichEditor` 存在
- [ ] 把某个模块的字段 `type` 改成 `'rich'`，刷新看到编辑器
- [ ] 输入文字，工具栏浮起
- [ ] 选中文字，B/I/U/字色 都能触发并显示激活态
- [ ] 字体下拉切换有效
- [ ] 字号手动输入有效
- [ ] `'rich-image'` 类型可以插入图片
- [ ] 图片可以 8 方向拖拽改尺寸
- [ ] 段落对齐三按钮影响图片位置
- [ ] 保存模块后，浏览器 Network 看 PUT 请求 payload 里 `*_html` 字段是清洗后的 HTML
- [ ] 后端日志无 sanitize 警告

---

## 9. 后续可扩展点（不在本次范围）

1. **粘贴 Word 内容**：写自定义 `pasteHandler`，用 `juice` 把 Word 的内联 style 处理掉
2. **格式刷**：选中 → 复制 marks → 应用到下一选区
3. **协同编辑**：Tiptap 自带 Yjs 集成（如需要多人编辑海报）
4. **导出 docx**：Tiptap → mammoth 反向，但海报场景一般不需要
5. **企业字体本地化**：把腾讯体 ttf 放进 `static/fonts/`，用 `@font-face` 加载（CDN 字体加载慢时）

---

## 10. 联系人

- 本次升级讨论纪要：`MEMORY.md`（在 WorkBuddy 项目根）
- Demo 参考（独立可跑的网易邮箱风版）：`/Users/dorrain/WorkBuddy/2026-06-25-11-16-38/netease-style-editor.html`
- 升级负责人：Dorrain（腾讯 IEG 成都）

---

**就这些。**祝集成顺利。
