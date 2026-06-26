# 平台化重构报告

## 1. 原始启动入口

原始启动入口为：

```text
poster-web/serve.py
```

已确认：

- 使用 `FastAPI()`
- 使用 `uvicorn.run`
- 挂载 `StaticFiles(directory=ROOT / "static")`
- 根路径 `/` 返回 `static/index.html`
- 默认端口保持 `8765`

## 2. 新启动方式

保持不变：

```bash
cd poster-web
python3 serve.py
```

## 3. 前端拆分

新增结构：

```text
poster-web/static/app-shell/
poster-web/static/shared/
poster-web/static/editor-core/
poster-web/static/skills/poster/
poster-web/frontend/
```

`static/app.js` 已从大业务文件改为平台启动器。原大文件移动到：

```text
poster-web/static/app-shell/legacy-app-adapter.js
```

存在兼容 adapter 的原因：原页面已有大量 Vue 状态、海报模块编辑、AI 文案、生图、artifact 和导出逻辑，直接一次性硬拆会极高概率破坏可运行链路。本次先完成平台壳、skill registry、editor-core、poster skill 入口，并由 adapter 保留全部旧功能。后续迁移方向是逐步把 `legacy-app-adapter.js` 中的 poster 逻辑移动到 `skills/poster/*`。

## 4. 后端拆分

新增：

```text
poster-web/backend/routers/
poster-web/backend/services/
poster-web/backend/repositories/
poster-web/backend/schemas/
poster-web/backend/core/
```

旧接口仍由以下文件保留：

```text
api.py
projects_api.py
config_api.py
kb_api.py
```

新平台接口挂载在：

```text
/api/platform/*
```

## 5. Poster Skill

前端 poster skill 位于：

```text
poster-web/static/skills/poster/
```

注册表：

```text
poster-web/static/skills/registry.json
```

manifest：

```text
poster-web/static/skills/poster/manifest.json
```

## 6. Editor Core

通用富文本能力位于：

```text
poster-web/static/editor-core/
```

包含：

- TipTap 创建
- posterImage 节点
- toolbar 命令
- editor_json 序列化
- legacy HTML 兼容
- 上传适配

## 7. gaming-training-poster 接入

旧入口保持：

```python
from lib import components
```

新增模块化入口：

```text
gaming-training-poster/scripts/lib/renderers/
gaming-training-poster/scripts/lib/rich/
gaming-training-poster/scripts/lib/layout_core/
```

富文本优先级保留：

```text
editor_json > content_html > content
```

## 8. 保留旧接口

保留旧前端使用的接口，包括：

- `GET/POST /api/projects`
- `GET/PUT/DELETE /api/projects/{pid}`
- `GET/POST/PUT/DELETE /api/projects/{pid}/function-projects/...`
- `GET /api/projects/{pid}/artifacts`
- `GET /api/skills`
- `POST /api/upload`
- `GET /api/asset/...`
- `GET /api/skill-asset...`
- `GET/POST /api/config...`
- `GET/POST /api/kb...`

## 9. 已测试

见 `TEST_REPORT.md`。

## 10. 仍需人工浏览器验收

- 真实项目编辑保存
- TipTap 选区、图片 8 方向缩放的实际交互手感
- 真实海报生成视觉结果
- PDF 导出文件内容
- LLM/生图模型真实 API 调用

## 11. Adapter 迁移方向

短期：

- 禁止继续向 `legacy-app-adapter.js` 加新功能。
- 新 skill 只通过 `skills/registry.json` 和独立 skill 目录接入。

中期：

- 将 poster 状态迁移到 `skills/poster/poster-state.js`
- 将 poster API 迁移到 `skills/poster/poster-api.js`
- 将模块编辑迁移到 `skills/poster/poster-editor.js`
- 将预览/生成迁移到 `skills/poster/poster-preview.js` 和 `poster-jobs.js`

