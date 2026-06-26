# IEG 人才发展项目管理 AI 工作台：平台化重构版启动说明

## 启动

```bash
cd poster-web
python3 serve.py
```

默认地址：

```text
http://127.0.0.1:8765
```

如需指定端口：

```bash
PORT=8766 python3 serve.py --no-browser
```

## 保留能力

- 原有首页、项目列表、项目详情页仍走原页面。
- 原有海报子项目、文案生成、模块编辑、TipTap 富文本、图片插入/缩放/删除、海报预览、PNG/PDF 导出仍由 legacy adapter 承接。
- 新的前端平台壳会先加载 `static/skills/registry.json`，再加载 poster skill，然后启动旧兼容适配层。
- 旧 API 全部保留，新平台化 API 额外挂在 `/api/platform/*`。

## 重要目录

```text
poster-web/static/app.js                         平台启动入口
poster-web/static/app-shell/                     平台壳
poster-web/static/shared/                        通用工具
poster-web/static/editor-core/                   富文本 editor-core
poster-web/static/skills/poster/                 poster skill 前端
poster-web/static/app-shell/legacy-app-adapter.js 旧前端兼容适配层

poster-web/backend/routers/                      模块化后端 router
poster-web/backend/services/                     模块化 service
poster-web/backend/repositories/                 文件型 repository

gaming-training-poster/scripts/lib/renderers/    渲染器模块入口
gaming-training-poster/scripts/lib/rich/         富文本渲染入口
gaming-training-poster/scripts/lib/layout_core/  布局基础工具
```

