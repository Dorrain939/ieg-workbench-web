# 测试报告

## 已执行测试

### 1. Python 语法检查

执行：

```bash
PYTHONPYCACHEPREFIX=/private/tmp/ieg_pycache python3 -m py_compile \
  poster-web/serve.py \
  poster-web/projects_api.py \
  poster-web/api.py \
  poster-web/backend/routers/*.py \
  poster-web/backend/services/*.py \
  poster-web/backend/repositories/*.py \
  poster-web/skills/strategy_bridge.py \
  gaming-training-poster/scripts/compose_poster_v2.py \
  gaming-training-poster/scripts/lib/renderers/*.py \
  gaming-training-poster/scripts/lib/rich/*.py \
  gaming-training-poster/scripts/lib/layout_core/*.py
```

结果：通过。

### 2. 前端语法检查

执行：

```bash
node --check poster-web/static/app.js
node --check poster-web/static/app-shell/legacy-app-adapter.js
```

结果：通过。

### 3. 前端 smoke

执行：

```bash
cd poster-web/frontend
node tests/smoke.mjs
```

结果：`frontend smoke ok`。

### 4. 渲染端导入检查

执行了 `lib.renderers.*`、`lib.rich.*` 导入检查。

结果：`renderer imports ok`。

### 5. 海报渲染烟雾测试

执行：

```bash
cd gaming-training-poster
python3 scripts/compose_poster_v2.py --brief scripts/brief_ai-bootcamp-2026.json --out /private/tmp/poster_smoke_modular.png
```

结果：通过，生成：

```text
/private/tmp/poster_smoke_modular.png
/private/tmp/poster_smoke_modular.pdf
```

PNG 体积约 2.9MB。

### 6. 服务启动

执行：

```bash
cd poster-web
python3 serve.py --no-browser
```

结果：通过，监听：

```text
http://127.0.0.1:8765
```

### 7. HTTP 接口检查

由于当前 Codex 沙箱对本地 socket 有限制，使用提升权限后的 Python urllib 检查。

结果：

```text
200 http://127.0.0.1:8765/
200 http://127.0.0.1:8765/healthz
200 http://127.0.0.1:8765/static/app.js
200 http://127.0.0.1:8765/static/skills/registry.json
200 http://127.0.0.1:8765/api/projects
200 http://127.0.0.1:8765/api/platform/skills
```

## 仍需人工浏览器验收

- 项目详情进入海报功能
- TipTap 实际选区编辑、图片 8 方向缩放手感
- 保存海报子项目
- 生成海报预览
- PNG/PDF 从浏览器导出
- 真实 LLM/生图 API 调用
