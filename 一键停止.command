#!/bin/bash
cd "$(dirname "$0")/poster-web"

PID_FILE=".server.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID" 2>/dev/null
        sleep 1
        ps -p "$PID" > /dev/null 2>&1 && kill -9 "$PID" 2>/dev/null
        echo "✓ 已停止 PID=$PID"
    fi
    rm -f "$PID_FILE"
fi

# 兜底
PORT_PID=$(lsof -ti:8765 2>/dev/null || true)
if [ -n "$PORT_PID" ]; then
    kill -9 $PORT_PID 2>/dev/null || true
    echo "✓ 已强制停止 8765 端口的进程"
fi

echo "服务已停止"
sleep 2
