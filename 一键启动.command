#!/bin/bash
# 一键启动 IEG 培训海报 AI 工作台
# 用法：双击此文件 或 终端执行 ./一键启动.command

set -e
cd "$(dirname "$0")"

echo "════════════════════════════════════════════════"
echo "  🎨  IEG 培训海报 AI 工作台 · 一键启动"
echo "════════════════════════════════════════════════"
echo ""

# ─── 1. 选 Python ───
PYTHON_BIN="/Library/Developer/CommandLineTools/usr/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi
echo "✓ 使用 Python：$PYTHON_BIN"
$PYTHON_BIN --version

# ─── 2. 检查 skill 是否到位 ───
SKILL_DIR="$HOME/.codebuddy/skills/gaming-training-poster"
if [ ! -d "$SKILL_DIR" ]; then
    echo ""
    echo "⚠️  未找到 skill 目录：$SKILL_DIR"
    echo "    需要从备份恢复 skill。看本目录是否有 gaming-training-poster/"
    if [ -d "./gaming-training-poster" ]; then
        echo "    ✓ 检测到本地 skill，正在复制到 ~/.codebuddy/skills/..."
        mkdir -p "$HOME/.codebuddy/skills"
        cp -R "./gaming-training-poster" "$HOME/.codebuddy/skills/"
        echo "    ✓ skill 已恢复"
    else
        echo "    ❌ 找不到 skill，无法启动渲染。请联系开发者。"
        exit 1
    fi
fi
echo "✓ skill 目录：$SKILL_DIR"

# ─── 3. 检查 LLM 配置 ───
CONFIG_DIR="$HOME/.poster-web"
CONFIG_FILE="$CONFIG_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    if [ -f "./dotfiles/poster-web-config.json" ]; then
        echo "✓ 从备份恢复 LLM 配置..."
        mkdir -p "$CONFIG_DIR"
        cp "./dotfiles/poster-web-config.json" "$CONFIG_FILE"
        chmod 600 "$CONFIG_FILE"
    else
        echo "ℹ️  首次启动：LLM 配置为空，启动后请在网页右上角 ⚙️ 填 DeepSeek API Key"
    fi
else
    echo "✓ LLM 配置：$CONFIG_FILE"
fi

# ─── 4. 检查依赖 ───
echo ""
echo "检查 Python 依赖..."
cd poster-web
MISSING=""
for pkg in fastapi uvicorn jieba pypdf docx pptx rank_bm25 PIL; do
    if ! $PYTHON_BIN -c "import $pkg" 2>/dev/null; then
        MISSING="$MISSING $pkg"
    fi
done

if [ -n "$MISSING" ]; then
    echo "  缺失：$MISSING"
    echo "  正在安装依赖（pip install -r requirements.txt）..."
    $PYTHON_BIN -m pip install -q -r requirements.txt
fi
echo "✓ 依赖齐全"

# ─── 5. 处理已运行的服务 ───
PID_FILE=".server.pid"
if [ -f "$PID_FILE" ]; then
    OLD=$(cat "$PID_FILE")
    if ps -p "$OLD" > /dev/null 2>&1; then
        echo ""
        echo "✓ 服务已在运行 PID=$OLD"
        echo ""
        echo "→ 访问 http://127.0.0.1:8765"
        open "http://127.0.0.1:8765"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

# 兜底：杀掉占用 8765 的进程
PORT_PID=$(lsof -ti:8765 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
    echo "  发现 8765 端口被占用 ($PORT_PID)，先停掉..."
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 1
fi

# ─── 6. 启动 ───
echo ""
echo "启动服务..."
nohup "$PYTHON_BIN" serve.py --no-browser > server.log 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

# 等服务起来
sleep 2
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "❌ 启动失败！查看日志：cat $(pwd)/server.log"
    tail -20 server.log
    rm -f "$PID_FILE"
    exit 1
fi

echo "✓ 服务已启动 PID=$PID"
echo "  日志：tail -f $(pwd)/server.log"
echo "  停止：./一键停止.command"
echo ""
echo "════════════════════════════════════════════════"
echo "  ➡  http://127.0.0.1:8765"
echo "════════════════════════════════════════════════"

# 打开浏览器
sleep 1
open "http://127.0.0.1:8765"
