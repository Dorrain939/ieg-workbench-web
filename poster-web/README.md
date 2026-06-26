# IEG 海报拼搭器（Web 前端）

> v0.1 MVP · 基于既有 `gaming-training-poster` skill，提供拖拽式 Web UI 编辑海报。

## 启动方式

```bash
cd ~/Desktop/poster-web

# 1. 安装依赖（首次）
pip3 install -r requirements.txt

# 2. 启动（自动打开浏览器）
python3 serve.py
```

默认监听 `http://127.0.0.1:8765`。

如不希望自动开浏览器：`python3 serve.py --no-browser`
改端口：`PORT=9000 python3 serve.py`

## 前置条件

- 必须装好 skill：`~/.codebuddy/skills/gaming-training-poster/`
- Python 3.9+
- 字体已就位：`<skill>/assets/fonts/TencentSans-W3.ttf`、`W7.ttf`

## 使用流程

1. **载入模板**：顶部下拉选 `brief_vfx-bootcamp-2026` 等任意模板，作为起点
2. **编辑画布**：点中间最上方"画布与全局配置"卡，右侧调整配色、底图、底层装饰
3. **编辑模块**：左侧点⊕添加 section / 中间拖拽 ≡ 排序 / 点 × 删除 / 点击进入右侧编辑
4. **上传素材**：file 字段右边点"上传"按钮，PNG/JPG 直接上传到本会话目录
5. **点击"🚀 渲染"**：约 5-10 秒后弹窗显示完整海报，可下载 PNG/PDF

## 目录结构

```
poster-web/
├── serve.py            FastAPI + 自动开浏览器（启动入口）
├── api.py              10 个 REST API 端点
├── schemas.py          12 个 section 类型 + canvas 字段表单 schema
├── requirements.txt    fastapi / uvicorn / pillow
├── static/
│   ├── index.html      Vue 3 单页 + Sortable 拖拽
│   └── app.js          前端业务逻辑 + 通用字段表单组件
├── uploads/            会话上传素材（按 session_id 隔离）
├── outputs/            渲染产物（按 job_id 隔离）
└── README.md
```

## API 端点速查

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/schemas` | 所有 section 字段表单定义 + canvas |
| GET | `/api/templates` | skill 内现有 brief 模板列表 |
| GET | `/api/template/{name}` | 某个模板的 JSON 内容 |
| POST | `/api/upload` | 上传素材（form-data：file + session_id） |
| GET | `/api/asset/{sid}/{fn}` | 预览上传的素材 |
| GET | `/api/skill-uploads` | skill 既有素材库（分场景） |
| GET | `/api/skill-asset?path=` | 访问 skill 内的素材文件 |
| POST | `/api/render` | 渲染海报（body：`{brief, session_id}`） |
| GET | `/api/preview/{job_id}/poster.png` | 下载渲染产物 |
| POST | `/api/new-session` | 创建新会话 ID |

## 支持的 Section 类型（v0.1）

| Type | 说明 |
|---|---|
| `top_logo_bar` | 顶部 logo 横幅 |
| `hero_strip` | 主标题艺术字 |
| `subtitle_text` | 副标题 |
| `section_title_bar` | 模块标题（白字下划线） |
| `lead_paragraph` | 段落正文（4 种面板样式） |
| `image_block` | 图片块 |
| `data_table` | 数据表格 |
| `faculty_grid` | 讲师团 / 顾问团（4 种布局） |
| `notice_box` | 注意事项（支持单条标红） |
| `contact_inline` | 联系方式 |
| `info_card` | 信息卡（带 logo） |
| `cta_button` | CTA 大按钮 |

复杂表格 `complex_table`、Playwright `table_module`、`info_card_with_qr` 等待 v0.2。

## 已知限制

- **渲染同步阻塞**：单次约 5-10s，期间 UI 显示 loading
- **素材库选择面板**未实现，目前只能"上传"或粘贴绝对路径
- **配色方案**只列了选项，无可视化预览
- **PDF 下载**：引擎默认输出 PDF，但实际是 PNG 嵌入容器，分辨率不会更高
- **字体许可**：腾讯体仅限内部使用，不要外发

## 后续迭代

v0.2：
- 素材库选择面板（侧边可视化挑图）
- 增量渲染（只重画变动 section，速度提升 3-5 倍）
- 配色预览缩略图
- 移动端响应式

v0.3：
- AI 助手（自然语言生 brief）
- 多人协作 / 版本管理
- 部署到内网 + 鉴权
