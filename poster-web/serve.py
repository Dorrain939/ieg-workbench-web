"""单命令启动：python serve.py"""
import os
import sys
import webbrowser
import threading
import time
import pathlib
import re
import shutil

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app_paths import WEB_ROOT as ROOT  # noqa: E402
from app_db import init_app_db  # noqa: E402

sys.path.insert(0, str(ROOT))

from api import router as api_router  # noqa: E402
from projects_api import router as projects_router  # noqa: E402
from config_api import router as config_router  # noqa: E402
from kb_api import router as kb_router  # noqa: E402
from backend.routers import platform_router  # noqa: E402

app = FastAPI(title="IEG 海报拼搭器", version="0.3.0")
app.include_router(api_router)
app.include_router(projects_router)
app.include_router(config_router)
app.include_router(kb_router)
app.include_router(platform_router)

# 静态文件
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


def _current_boot_version() -> str:
    app_js = ROOT / "static" / "app.js"
    try:
        text = app_js.read_text(encoding="utf-8")
    except Exception:
        return "unknown"
    match = re.search(r'BOOT_VERSION\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else "unknown"


def _clear_directory_contents(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink(missing_ok=True)


def _clear_history_for_update(force: bool = False) -> None:
    """清空历史项目/上传/产物数据，保留功能源码。

    用户要求每次更新都清空历史材料，因此这里以 static/app.js 的
    BOOT_VERSION 为更新指纹。版本变化时自动清空；设置
    IEG_KEEP_HISTORY=1 可在开发排障时临时跳过。
    """
    if os.environ.get("IEG_KEEP_HISTORY") == "1":
        return

    version = _current_boot_version()
    marker = ROOT / ".history_reset_version"
    previous = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""
    if not force and previous == version:
        return

    project_root = ROOT.parent
    data_dirs = [
        ROOT / "projects",
        ROOT / "uploads",
        ROOT / "covers" / "generated",
        ROOT / "static" / "covers" / "generated",
        ROOT / "kb_data" / "projects",
        ROOT / "kb_data" / "_tmp_recognize",
        project_root / "gaming-training-poster" / "assets" / "uploads",
    ]
    for path in data_dirs:
        _clear_directory_contents(path)

    sqlite_path = ROOT / "ieg_workbench.sqlite3"
    sqlite_path.unlink(missing_ok=True)

    for pycache in ROOT.rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)

    marker.write_text(version, encoding="utf-8")


@app.get("/")
def root():
    index = ROOT / "static" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"error": "未找到 static/index.html"}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.on_event("startup")
def _startup():
    _clear_history_for_update()
    init_app_db()


def _open_browser(url: str, delay: float = 1.0):
    """延迟打开浏览器，等服务起来。"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    url = f"http://{host}:{port}"

    if "--no-browser" not in sys.argv:
        threading.Thread(target=_open_browser, args=(url,), daemon=True).start()

    print(f"\n  🎨  IEG 海报拼搭器  →  {url}\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
