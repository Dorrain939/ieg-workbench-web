# ieg-workbench-web

一个关于 IEG TD 项目管理的平台，有海报、PPT 等功能。

# 🎨 IEG 培训海报 AI 工作台 · 备份与启动指南

> 备份时间：2026-06-07 19:42  
> 版本：v0.4 (海报系列双能力 + 知识库 RAG + 项目工作台)

## 📦 这个文件夹是什么

完整的工作台备份，包含：

```
poster-web-backup-20260607-194209/
├── 一键启动.command          ← 双击启动（macOS）
├── 一键停止.command          ← 双击停止
├── README.md                ← 你正在看的这个文件
│
├── poster-web/              ← 主程序（Python 后端 + Vue 前端）
│   ├── serve.py             启动入口
│   ├── api.py               主 API
│   ├── projects_api.py      项目管理 + skill 调用
│   ├── kb_api.py            知识库 API
│   ├── config_api.py        LLM 配置 API
│   ├── llm_client.py        DeepSeek 客户端
│   ├── llm_tools.py         编辑器 AI 改稿工具
│   ├── schemas.py           12 种海报板块 schema
│   │
│   ├── skills/              4 个 AI 工作场景
│   │   ├── copywriter.py        海报文案
│   │   ├── poster_brief.py      海报生成（含渲染）
│   │   ├── auto_project.py      AI 抽取项目信息
│   │   ├── runner.py            统一 SSE 流封装
│   │   └── registry.py          skill 注册表
│   │
│   ├── prompts/             所有 prompt（拆出来方便迭代）
│   │   ├── copywriter.txt
│   │   └── poster_brief.txt
│   │
│   ├── kb/                  知识库引擎
│   │   ├── loader.py            txt/md/pdf/docx/pptx 解析
│   │   ├── chunker.py           文本切片
│   │   └── index.py             BM25 检索
│   │
│   ├── static/              前端
│   │   ├── index.html
│   │   ├── app.js
│   │   ├── styles.css
│   │   └── covers/              8 张预制 SVG 封面
│   │
│   ├── projects/            ← 你的项目数据（含 9 个示例 + 已生成的产物）
│   ├── kb_data/             ← 知识库文档（已上传的 docx 等）
│   └── uploads/             海报编辑器素材
│
├── gaming-training-poster/  ← 海报渲染引擎（必须在 ~/.codebuddy/skills/ 下）
│   ├── scripts/
│   │   ├── compose_poster_v2.py  渲染主入口
│   │   ├── content_md_to_brief.py  md → brief 转换器
│   │   ├── gen_background.py       底图生成（image API）
│   │   └── lib/                    依赖库
│   ├── assets/                字体 / 模板素材（约 100MB）
│   └── references/            场景 prompt / 配色方案文档
│
└── dotfiles/
    └── poster-web-config.json  ← LLM 配置模板（请在本机填写 DeepSeek API key）
```

---

## 🚀 一键启动（macOS）

### 第一次使用（恢复到任何 Mac）

1. **解压**这个文件夹到任意位置（比如桌面）
2. **双击** `一键启动.command`
3. 终端窗口会自动：
   - 检测 Python 3.9+
   - 自动把 `gaming-training-poster/` 复制到 `~/.codebuddy/skills/`（如果不存在）
   - 自动恢复 `dotfiles/poster-web-config.json` 到 `~/.poster-web/config.json`
   - 自动 `pip install` 缺失的依赖
   - 启动服务并打开浏览器

如果第一次双击提示**「无法打开，因为它来自身份不明的开发者」**：
- 右键点击 `一键启动.command` → **打开** → 弹窗点「打开」即可
- 或在「系统设置 → 隐私与安全性」点「仍要打开」

### 日常使用

- **启动**：双击 `一键启动.command`
- **停止**：双击 `一键停止.command`
- **访问**：`http://127.0.0.1:8765`

服务起来后会自动开浏览器到首页。

---

## 🔧 手动启动（如果脚本不工作）

```bash
cd poster-web-backup-20260607-194209/

# 1. 把 skill 放到正确位置（首次）
cp -r gaming-training-poster ~/.codebuddy/skills/

# 2. 恢复 LLM 配置（首次）
mkdir -p ~/.poster-web
cp dotfiles/poster-web-config.json ~/.poster-web/config.json
chmod 600 ~/.poster-web/config.json

# 3. 装依赖
cd poster-web
/Library/Developer/CommandLineTools/usr/bin/python3 -m pip install -r requirements.txt

# 4. 启动
./start.sh

# 浏览器访问 http://127.0.0.1:8765
# 停止：./stop.sh
```

---

## 🪟 Windows / Linux 启动

`.command` 是 macOS 专属。其他系统手动跑：

```bash
# 1. 复制 skill 到 ~/.codebuddy/skills/gaming-training-poster/
# 2. 复制 dotfiles/poster-web-config.json 到 ~/.poster-web/config.json
# 3. 进入 poster-web/ 目录
cd poster-web
pip install -r requirements.txt
python serve.py
# 浏览器访问 http://127.0.0.1:8765
```

---

## ⚙️ 当前已有的能力

进入项目详情后，左侧二级导航能看到：

| 能力 | 状态 | 说明 |
|---|---|---|
| 📋 概览 | ✅ | 项目信息 + 4 张能力快捷卡 + 最近产物时间线 |
| ✍️ 海报文案 | ✅ | 基于项目 + 知识库自动生成符合渲染引擎约定的 markdown |
| 🎨 海报生成 | ✅ | 复用文案 → md_to_brief → compose_long_poster 真实渲染 PNG |
| 🖼️ 海报编辑器 | ✅ | 12 种 section 拖拽编辑器，可载入生成的 brief 继续手动改 |
| 🎤 访谈提纲 | 🚧 | 框架已就位，下版填实 |
| 📊 PPT 大纲 | 🚧 | 同上 |
| 📚 项目知识库 | ✅ | txt/md/pdf/docx/pptx 5 种格式上传，BM25 中文检索 |
| 📦 全部产物 | ✅ | 所有 AI 产物归档表格 |

外加：
- **「+ 新建项目」**：可直接上传文档 + AI 抽取项目信息预填表单
- **「⚙️ 设置」**（右上角）：填 DeepSeek API key 和 base_url
- **「💾 保存到项目」**（编辑器顶栏）：编辑器修改后保存为新版本 artifact

---

## 🔑 LLM 配置说明

**默认配置**（`~/.poster-web/config.json`）：
```json
{
  "deepseek_api_key": "sk-...",
  "deepseek_base_url": "https://api.deepseek.com/v1",
  "deepseek_model": "deepseek-chat"
}
```

如果 key 失效或想换：
1. 浏览器右上角 ⚙️ 按钮
2. 填新 key → 点「测试连接」→ 保存

---

## 🔧 常见问题

### Q: 双击 `.command` 没反应
- 右键 → 打开 → 系统会请求授权一次
- 或在终端 `chmod +x 一键启动.command` 后再双击

### Q: 端口 8765 被占用
- 双击 `一键停止.command` 强制释放
- 或 `lsof -ti:8765 | xargs kill -9`

### Q: 启动失败提示 "ModuleNotFoundError: No module named 'compose_poster_v2'"
- 检查 `~/.codebuddy/skills/gaming-training-poster/scripts/compose_poster_v2.py` 是否存在
- 用一键启动脚本会自动复制；手动启动需要先 `cp -r gaming-training-poster ~/.codebuddy/skills/`

### Q: 渲染海报报错 "FileNotFoundError: TencentSans-W3.ttf"
- 字体在 `gaming-training-poster/assets/fonts/`，必须随 skill 一起到 `~/.codebuddy/skills/` 下

### Q: 项目数据在哪
- `poster-web/projects/<pid>/project.json` + 各 artifact 子目录
- 直接 `tar` 这个文件夹就能整个备份/迁移

### Q: 怎么查日志
```bash
tail -f poster-web/server.log
```

---

## 📂 备份建议

整个文件夹（约 200MB）随时可拷走当备份：
- 关键数据在 `poster-web/projects/`、`poster-web/kb_data/`
- 配置在 `dotfiles/`
- skill 引擎在 `gaming-training-poster/`

定期把这个文件夹整个 zip 一份就是完整备份。

---

## 📞 升级路线（v0.5+）

- 访谈提纲、PPT 大纲、研究报告 skill
- nano_banana 主视觉底图（接外部 image API）
- 30 人协作（企业微信 SSO + Postgres + 任务队列）
- 真 .pptx 文件输出
