# -*- mode: python ; coding: utf-8 -*-
# macOS build — produces "Reference Checker.app" inside dist/
import os
import sys
from PyInstaller.utils.hooks import collect_all

APP_NAME = "Reference Checker"
APP_VERSION = "1.2.1"
EXE_NAME = "ReferenceChecker"
BUNDLE_ID = "com.kutzun.referencechecker"

datas = []
binaries = []
hiddenimports = []

if sys.platform == "win32":
    _py_ver = f"{sys.version_info.major}{sys.version_info.minor}"
    for _candidate in (
        os.path.join(sys.base_prefix, f"python{_py_ver}.dll"),
        os.path.join(sys.prefix, f"python{_py_ver}.dll"),
        os.path.join(os.path.dirname(sys.executable), f"python{_py_ver}.dll"),
    ):
        if os.path.isfile(_candidate):
            binaries.append((_candidate, "."))
            break
    else:
        raise SystemExit(f"python{_py_ver}.dll not found")

for package in ("nicegui", "uvicorn", "fastapi", "starlette", "pydantic"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["launcher.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["pyinstaller_hooks"],
    hooksconfig={},
    runtime_hooks=["pyinstaller_hooks/rthook_safe_streams.py"],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "pywebview", "matplotlib", "numpy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=EXE_NAME,
)

app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=None,
    bundle_identifier=BUNDLE_ID,
    info_plist={
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION + ".0",
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleExecutable": EXE_NAME,
        "CFBundlePackageType": "APPL",
        "NSHighResolutionCapable": "True",
        "LSMinimumSystemVersion": "12.0",
    },
)