# 迁移说明

## 数据兼容

旧字段继续保留：

```text
content
content_html
images
```

新字段继续支持：

```text
editor_json
content_editor_json
```

后端仍通过原 `projects_api.py` 的清洗逻辑处理富文本 HTML 和 editor_json。

## 接口兼容

旧接口不迁移路径，不改 HTTP Method。新模块化接口统一新增在 `/api/platform/*`。

## 前端兼容

旧 Vue 应用仍作为：

```text
static/app-shell/legacy-app-adapter.js
```

由平台启动器加载。这样保证原有海报编辑、生图、文案、导出等链路不被拆坏。

## 渲染兼容

旧 `components.py` 仍是 compose 链路的兼容入口。新增 `renderers/`、`rich/`、`layout_core/` 是后续逐步迁移的稳定导入层。

## 后续新增 Skill 规则

新增 PPT、报告、访谈等功能时：

1. 在 `poster-web/static/skills/registry.json` 增加 skill。
2. 新建 `poster-web/static/skills/<skill-id>/`。
3. 后端新增 `poster-web/backend/routers/<skill-id>.py` 和对应 service。
4. 不再修改 `legacy-app-adapter.js`。

