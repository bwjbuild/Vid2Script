# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Vid2Script .exe build.

Run on Windows:
    pip install pyinstaller
    pyinstaller vid2script.spec

Output: dist/Vid2Script.exe (single self-extracting .exe)
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Paths (relative to this spec file's location)
SPEC_DIR   = Path(SPECPATH)
PROJECT_DIR = SPEC_DIR
SCRIPT     = PROJECT_DIR / "vid2script.py"
FFMPEG_DIR = PROJECT_DIR / "ffmpeg"
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR    = PROJECT_DIR / "logs"

# Collect all data dirs that need to ship with the .exe
datas = []

if FFMPEG_DIR.exists():
    datas.append((str(FFMPEG_DIR), "ffmpeg"))   # ships as ./ffmpeg/ in the bundle
else:
    print("WARNING: ffmpeg/ folder not found. Run SETUP.bat first, then re-run build.bat")

# Empty output/ and logs/ dirs — created at runtime by the script
datas.append((str(OUTPUT_DIR), "output"))
datas.append((str(LOG_DIR),    "logs"))

a = Analysis(
    [str(SCRIPT)],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Tkinter is usually auto-detected, but list explicitly to be safe
        "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.ttk",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Vid2Script",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # ← Windowed app — no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Vid2Script",
)

# ── Single-file alternative (uncomment for onefile — slower first run) ─────────
# from PyInstaller.utils.hooks import collect_all
#
# datas   = []
# binaries = []
# if FFMPEG_DIR.exists():
#     datas.append((str(FFMPEG_DIR), "ffmpeg"))
#
# a = Analysis(
#     [str(SCRIPT)],
#     pathex=[str(PROJECT_DIR)],
#     hiddenimports=["tkinter", "tkinter.filedialog", "tkinter.messagebox", "tkinter.ttk"],
#     datas=datas,
#     binaries=binaries,
# )
# pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
# exe = EXE(pyz, a.scripts, [], console=False, name="Vid2Script")
