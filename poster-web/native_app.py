"""macOS native desktop entry: FastAPI backend + PyWebView shell."""
from __future__ import annotations

import os
import pathlib
import shutil
import socket
import sys
import threading
import time

import uvicorn
import webview


def _prepare_paths() -> pathlib.Path:
    if getattr(sys, "frozen", False):
        base = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(sys.executable).resolve().parent))
        web_root = base / "poster-web"
        if web_root.exists():
            sys.path.insert(0, str(web_root))
            return web_root
    web_root = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(web_root))
    return web_root


def _free_port() -> int:
    for port in (8766, 8765, 8767, 8768):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


WEB_ROOT = _prepare_paths()
DATA_ROOT = pathlib.Path.home() / "Library" / "Application Support" / "IEGWorkbench"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("POSTER_WEB_NATIVE", "1")
os.environ.setdefault("POSTER_WEB_DATA_DIR", str(DATA_ROOT))


def _copytree_once(src: pathlib.Path, dst: pathlib.Path) -> None:
    if not src.exists() or dst.exists():
        return
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", ".server.pid", "server.log"))


def _seed_user_data_once() -> None:
    marker = DATA_ROOT / ".initial_data_seeded"
    if marker.exists():
        return
    for name in ("projects", "uploads", "outputs", "kb_data"):
        _copytree_once(WEB_ROOT / name, DATA_ROOT / name)
    _copytree_once(WEB_ROOT / "static" / "covers" / "generated", DATA_ROOT / "covers" / "generated")
    marker.write_text("seeded\n", encoding="utf-8")


_seed_user_data_once()

from serve import app  # noqa: E402


def _run_server(port: int) -> None:
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def main() -> None:
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    thread.start()
    time.sleep(1.0)

    webview.create_window(
        "IEG 人才发展项目管理 AI 工作台",
        url,
        width=1440,
        height=960,
        min_size=(1180, 760),
        confirm_close=False,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
