#!/bin/bash
# 启动海报拼搭器（独立后台进程，不会被 codebuddy 回收）
cd "$(dirname "$0")"

# 优先用系统 python3.9（已装齐依赖），避免 brew python3.14 的 libexpat 兼容问题
PYTHON_BIN="/Library/Developer/CommandLineTools/usr/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN="python3"

PID_FILE=".server.pid"

# 已经在跑？
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if ps -p "$OLD_PID" > /dev/null 2>&1; then
    echo "✓ 服务已在运行，PID=$OLD_PID"
    echo "  访问 http://127.0.0.1:8765"
    echo "  停止：./stop.sh"
    exit 0
  else
    rm "$PID_FILE"
  fi
fi

# 启动
nohup "$PYTHON_BIN" serve.py --no-browser > server.log 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

sleep 1.5

if ps -p "$PID" > /dev/null 2>&1; then
  echo "✓ 已启动 PID=$PID"
  echo "  访问 http://127.0.0.1:8765"
  echo "  日志：tail -f $(pwd)/server.log"
  echo "  停止：./stop.sh"
  open "http://127.0.0.1:8765"
else
  echo "✗ 启动失败，看日志：cat $(pwd)/server.log"
  rm "$PID_FILE"
  exit 1
fi
