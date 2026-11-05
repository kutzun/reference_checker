# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Locate the Python DLL dynamically. The v1.2.1 spec hardcoded
# C:\Users\Lenovo\anaconda3\python312.dll, which only works on the
# developer's own machine — anyone else building from source, or the
# same developer from a fresh venv, hits a FileNotFoundError here.
# Compute the path from the running interpreter instead, so the
# spec works from any Python 3.12 install (conda, venv, system).
_py_dll_name = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
_py_dll_candidates = [
    Path(sys.executable).parent / _py_dll_name,
    Path(sys.base_prefix) / _py_dll_name,
]
_py_dll = next((p for p in _py_dll_candidates if p.exists()), None)
if _py_dll is not None:
    binaries.append((str(_py_dll), "."))

# Collect packages that ship their own data files or import submodules
# dynamically. The five web-stack packages were already in v1.2.1.
# `docx`, `certifi`, and `requests` are added in v1.2.2 to guard
# against the two most common frozen-build failures for this stack:
#
#   * certifi: HTTPS requests need the bundled CA certificate store
#     (cacert.pem). Without it, every provider call fails with
#     SSL: CERTIFICATE_VERIFY_FAILED in the frozen build, even
#     though it works fine from the source tree.
#   * python-docx: DOCX parsing needs the internal template files
#     (docx/templates/*.docx). Without them, python-docx raises
#     PackageNotFoundError on the first Document() call.
#
# PyInstaller's built-in hooks usually catch both, but explicit
# collect_all() makes the dependency visible in the spec — the same
# reason nicegui/uvicorn/fastapi/starlette/pydantic are already
# listed here.
for package in (
    'nicegui',
    'uvicorn',
    'fastapi',
    'starlette',
    'pydantic',
    'docx',
    'certifi',
    'requests',
):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['launcher.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['pyinstaller_hooks'],   # custom empty hook for 'workflow'
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'pywebview', 'matplotlib', 'numpy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ReferenceChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='ReferenceChecker',
)