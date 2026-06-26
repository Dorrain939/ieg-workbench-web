#!/bin/bash
# 构建 Apple 芯片 Mac 原生 .app / .dmg

set -e
cd "$(dirname "$0")"

APP_TITLE="IEG 人才发展项目管理 AI 工作台"
PYTHON_BIN="/Library/Developer/CommandLineTools/usr/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi

echo "================================================"
echo "  $APP_TITLE"
echo "  构建 macOS 原生应用"
echo "================================================"
echo ""

if [ -z "$PYTHON_BIN" ]; then
  echo "没有找到 python3。请先安装 Python 3 或 Xcode Command Line Tools。"
  read -p "按回车退出..."
  exit 1
fi

if [ "$(uname -m)" != "arm64" ]; then
  echo "警告：当前不是 Apple 芯片 arm64 环境，构建出来的包可能不是 Apple 芯片原生。"
fi

if [ ! -d ".build-venv" ]; then
  "$PYTHON_BIN" -m venv .build-venv
fi

source .build-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r poster-web/requirements.txt

rm -rf build dist
pyinstaller --clean --noconfirm IEGWorkbench-macos.spec

APP_PATH="dist/IEG 人才发展项目管理 AI 工作台.app"
if [ ! -d "$APP_PATH" ]; then
  echo "没有找到构建产物：$APP_PATH"
  exit 1
fi

OUT_DIR="$HOME/Desktop/IEGWorkbench-macOS-native"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
ditto "$APP_PATH" "$OUT_DIR/IEG 人才发展项目管理 AI 工作台.app"

DMG_PATH="$HOME/Desktop/IEGWorkbench-macOS-native.dmg"
rm -f "$DMG_PATH"
hdiutil create -volname "IEGWorkbench" -srcfolder "$OUT_DIR" -ov -format UDZO "$DMG_PATH"

echo ""
echo "构建完成："
echo "App: $OUT_DIR/IEG 人才发展项目管理 AI 工作台.app"
echo "DMG: $DMG_PATH"
echo ""
echo "说明：这个包未做 Apple Developer ID 签名和公证，发给同事后第一次打开仍可能需要右键打开。"
read -p "按回车退出..." || true
