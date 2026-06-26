#!/bin/bash
# 停止本交付包启动的 IEG 人才发展项目管理 AI 工作台

cd "$(dirname "$0")/poster-web" || exit 1

PID_FILE=".server.pid"
if [ ! -f "$PID_FILE" ]; then
  echo "没有找到运行中的服务记录。"
  read -p "按回车退出..."
  exit 0
fi

PID="$(cat "$PID_FILE")"
if ps -p "$PID" >/dev/null 2>&1; then
  kill "$PID" 2>/dev/null || true
  sleep 1
  if ps -p "$PID" >/dev/null 2>&1; then
    kill -9 "$PID" 2>/dev/null || true
  fi
  echo "已停止服务：PID=$PID"
else
  echo "服务进程已经不存在。"
fi

rm -f "$PID_FILE"
read -p "按回车退出..."
