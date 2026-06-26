"""Runtime paths for source mode and packaged macOS app mode."""
from __future__ import annotations

import os
import pathlib
import sys


APP_NAME = "IEGWorkbench"


def _resource_root() -> pathlib.Path:
    base = pathlib.Path(getattr(sys, "_MEIPASS", pathlib.Path(__file__).resolve().parent))
    bundled_web = base / "poster-web"
    if bundled_web.exists():
        return bundled_web
    return pathlib.Path(__file__).resolve().parent


def _default_data_root() -> pathlib.Path:
    if os.environ.get("POSTER_WEB_NATIVE") == "1":
        return pathlib.Path.home() / "Library" / "Application Support" / APP_NAME
    return WEB_ROOT


WEB_ROOT = _resource_root()
PACKAGE_ROOT = WEB_ROOT.parent
DATA_ROOT = pathlib.Path(os.environ.get("POSTER_WEB_DATA_DIR") or _default_data_root())
DATA_ROOT.mkdir(parents=True, exist_ok=True)

PROJECTS_DIR = DATA_ROOT / "projects"
UPLOADS_DIR = DATA_ROOT / "uploads"
OUTPUTS_DIR = DATA_ROOT / "outputs"
KB_DATA_DIR = DATA_ROOT / "kb_data"
GENERATED_COVERS_DIR = DATA_ROOT / "covers" / "generated"
SQLITE_PATH = DATA_ROOT / "ieg_workbench.sqlite3"

for path in (PROJECTS_DIR, UPLOADS_DIR, OUTPUTS_DIR, KB_DATA_DIR, GENERATED_COVERS_DIR):
    path.mkdir(parents=True, exist_ok=True)
