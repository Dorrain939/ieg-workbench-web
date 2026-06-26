#!/bin/bash
# 一键安装并启动 IEG 人才发展项目管理 AI 工作台

set -e
cd "$(dirname "$0")"

APP_NAME="IEG 人才发展项目管理 AI 工作台"
PYTHON_BIN="/Library/Developer/CommandLineTools/usr/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

echo "================================================"
echo "  $APP_NAME"
echo "  一键安装并启动"
echo "================================================"
echo ""

if [ -z "$PYTHON_BIN" ]; then
  echo "没有找到 python3。请先安装 Python 3 或 Xcode Command Line Tools。"
  read -p "按回车退出..."
  exit 1
fi

echo "Python: $PYTHON_BIN"
"$PYTHON_BIN" --version

if [ ! -d "poster-web" ]; then
  echo "缺少 poster-web 目录，请确认文件夹完整。"
  read -p "按回车退出..."
  exit 1
fi

if [ -d "./gaming-training-poster" ] && [ ! -d "$HOME/.codebuddy/skills/gaming-training-poster" ]; then
  echo "恢复 gaming-training-poster skill..."
  mkdir -p "$HOME/.codebuddy/skills"
  cp -R "./gaming-training-poster" "$HOME/.codebuddy/skills/"
fi

if [ -f "./dotfiles/poster-web-config.json" ] && [ ! -f "$HOME/.poster-web/config.json" ]; then
  echo "恢复模型配置..."
  mkdir -p "$HOME/.poster-web"
  cp "./dotfiles/poster-web-config.json" "$HOME/.poster-web/config.json"
  chmod 600 "$HOME/.poster-web/config.json"
fi

cd poster-web

if [ ! -d ".venv" ]; then
  echo "创建本地虚拟环境..."
  "$PYTHON_BIN" -m venv .venv
fi

source .venv/bin/activate

echo "安装/检查 Python 依赖..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

pick_port() {
  for p in 8766 8765 8767 8768; do
    if ! lsof -tiTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "$p"
      return
    fi
  done
  echo "8769"
}

PORT="$(pick_port)"
PID_FILE=".server.pid"

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE")"
  if ps -p "$OLD_PID" >/dev/null 2>&1; then
    echo "检测到本包服务已运行：PID=$OLD_PID"
    URL="http://127.0.0.1:${PORT}"
  else
    rm -f "$PID_FILE"
  fi
fi

if [ ! -f "$PID_FILE" ]; then
  echo "启动服务，端口：$PORT"
  PORT="$PORT" nohup python serve.py --no-browser > server.log 2>&1 &
  PID=$!
  echo "$PID" > "$PID_FILE"
  sleep 2
  if ! ps -p "$PID" >/dev/null 2>&1; then
    echo "启动失败，最近日志："
    tail -40 server.log
    rm -f "$PID_FILE"
    read -p "按回车退出..."
    exit 1
  fi
  URL="http://127.0.0.1:${PORT}"
fi

echo ""
echo "启动完成：$URL"
echo "日志文件：$(pwd)/server.log"
echo "停止服务：双击同目录的 一键停止.command"
echo ""

open "$URL"
read -p "浏览器已打开。按回车关闭这个窗口，服务会继续在后台运行..."
