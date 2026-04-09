# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for a single-file Windows release.
This avoids common support issues where users copy only the EXE from an onedir build
and then hit "failed to load python dll".
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

block_cipher = None

PROJECT_DIR = Path(SPECPATH)
SCRIPT = PROJECT_DIR / "vid2script.py"
FFMPEG_DIR = PROJECT_DIR / "ffmpeg"
OUTPUT_DIR = PROJECT_DIR / "output"
LOG_DIR = PROJECT_DIR / "logs"

hiddenimports = collect_submodules("yt_dlp")

datas = []
datas += copy_metadata("yt_dlp")

if FFMPEG_DIR.exists():
    datas.append((str(FFMPEG_DIR), "ffmpeg"))
else:
    print("WARNING: ffmpeg/ folder not found. Run SETUP.bat first.")

# Keep directories present in development and in frozen runtime.
datas.append((str(OUTPUT_DIR), "output"))
datas.append((str(LOG_DIR), "logs"))

a = Analysis(
    [str(SCRIPT)],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Vid2Script",
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
