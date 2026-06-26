# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


datas = [
    ("poster-web", "poster-web"),
    ("gaming-training-poster", "gaming-training-poster"),
]

hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("fastapi")
    + collect_submodules("starlette")
    + collect_submodules("webview")
    + [
        "PIL._tkinter_finder",
        "openpyxl",
        "pandas",
        "docx",
        "pptx",
        "pypdf",
        "rank_bm25",
        "jieba",
    ]
)


a = Analysis(
    ["poster-web/native_app.py"],
    pathex=["poster-web"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IEGWorkbench",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IEGWorkbench",
)

app = BUNDLE(
    coll,
    name="IEG 人才发展项目管理 AI 工作台.app",
    icon=None,
    bundle_identifier="com.ieg.talent.workbench",
    info_plist={
        "CFBundleName": "IEG 人才发展项目管理 AI 工作台",
        "CFBundleDisplayName": "IEG 人才发展项目管理 AI 工作台",
        "CFBundleShortVersionString": "2026.06.15",
        "CFBundleVersion": "2026.06.15",
        "NSHighResolutionCapable": True,
    },
)
