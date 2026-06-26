#!/bin/bash
cd "$(dirname "$0")"
PID_FILE=".server.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "未找到 PID 文件，可能服务未在运行"
  # 兜底：杀掉占用 8765 端口的进程
  PORT_PID=$(lsof -ti:8765 2>/dev/null)
  if [ -n "$PORT_PID" ]; then
    kill -9 $PORT_PID
    echo "✓ 已强制停止占用 8765 端口的进程 $PORT_PID"
  fi
  exit 0
fi

PID=$(cat "$PID_FILE")
if ps -p "$PID" > /dev/null 2>&1; then
  kill "$PID"
  sleep 1
  ps -p "$PID" > /dev/null 2>&1 && kill -9 "$PID"
  echo "✓ 已停止 PID=$PID"
fi
rm -f "$PID_FILE"
