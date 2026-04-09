#!/usr/bin/env python3
"""
Vid2Script — Video to MP3 Converter
Converts video files to MP3 (128 kbps) using FFmpeg.
Drag-and-drop or paste a video file path to convert.
"""

import os
import sys
import subprocess
import shutil
import logging
import re
import zipfile
from pathlib import Path
from datetime import datetime

# ─── Constants ────────────────────────────────────────────────────────────────

SCRIPT_DIR   = Path(__file__).parent.resolve()
FFMPEG_DIR   = SCRIPT_DIR / "ffmpeg"
FFMPEG_BIN   = FFMPEG_DIR / "ffmpeg.exe"
FFMPEG_URL   = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
OUTPUT_DIR   = SCRIPT_DIR / "output"
LOG_DIR      = SCRIPT_DIR / "logs"

SUPPORTED_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"}

# ─── Logging ───────────────────────────────────────────────────────────────────

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"vid2script_{datetime.now().strftime('%Y-%m-%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("vid2script")

log = setup_logging()

# ─── ANSI Colors ───────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def print_banner():
    print(f"""
{CYAN}{BOLD}
  ██╗  ██╗███████╗██╗   ██╗██████╗  ██████╗ ███╗   ██╗
  ██╔ ██╔╝██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗████╗  ██║
  ██╔╝ ██╔╝█████╗   ╚████╔╝ ██████╔╝██║   ██║██╔██╗ ██║
  ██╔╝ ██╔╝██╔══╝    ╚██╔╝  ██╔══██╗██║   ██║██║╚██╗██║
  ██╔╝ ██╔╝███████╗   ██║   ██║  ██║╚██████╔╝██║ ╚████║
  ╚═╝  ╚═╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
{RESET}{BOLD}  Video → MP3 Converter (128 kbps){RESET}
  Drag-and-drop a video or paste its full path to convert.
""")

# ─── FFmpeg Check / Install ────────────────────────────────────────────────────

def ffmpeg_exists():
    return FFMPEG_BIN.exists()

def get_ffmpeg_version():
    try:
        result = subprocess.run(
            [str(FFMPEG_BIN), "-version"],
            capture_output=True, text=True, timeout=10
        )
        match = re.search(r"ffmpeg version ([^\s]+)", result.stdout)
        return match.group(1) if match else "unknown"
    except Exception:
        return None

def download_ffmpeg():
    print(f"\n{YELLOW}⚠ FFmpeg not found in the ffmpeg/ folder.{RESET}")
    print(f"\n  Recommended: Run {CYAN}SETUP.bat{RESET} first — it downloads")
    print(f"  both Python and FFmpeg automatically.\n")
    print(f"  OR manually download FFmpeg to the ffmpeg/ folder:")
    print(f"  1. Download: {FFMPEG_URL}")
    print(f"  2. Extract the ZIP")
    print(f"  3. Copy ffmpeg.exe into: {FFMPEG_DIR}/\n")
    input("Press Enter to exit...")
    sys.exit(1)

# ─── File Validation ───────────────────────────────────────────────────────────

def validate_input(path_str):
    """Validate that the path is a supported video file."""
    path_str = path_str.strip().strip('"').strip("'")
    p = Path(path_str)

    if not p.exists():
        return None, f"File not found: {path_str}"

    if not p.is_file():
        return None, "Path is not a file."

    if p.suffix.lower() not in SUPPORTED_EXTS:
        supported = ", ".join(sorted(SUPPORTED_EXTS))
        return None, f"Unsupported format '{p.suffix}'. Supported: {supported}"

    return p, None

# ─── Conversion ────────────────────────────────────────────────────────────────

def convert_to_mp3(input_path: Path):
    """Convert a video file to MP3 (128 kbps)."""
    output_name = input_path.stem + ".mp3"
    output_path = OUTPUT_DIR / output_name

    OUTPUT_DIR.mkdir(exist_ok=True)

    cmd = [
        str(FFMPEG_BIN),
        "-i",       str(input_path),
        "-codec:a", "libmp3lame",
        "-b:a",     "128k",
        "-vn",                     # strip video
        "-y",                     # overwrite output
        str(output_path),
    ]

    log.info(f"Converting: {input_path.name}")
    print(f"\n{CYAN}▶ ffmpeg -i \"{input_path.name}\" ...{RESET}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,   # 10 min max for very large files
        )

        if result.returncode != 0:
            log.error(f"FFmpeg error: {result.stderr}")
            return None, f"FFmpeg failed:\n{result.stderr[-500:]}"

        if not output_path.exists():
            return None, "Output file was not created."

        size_kb = output_path.stat().st_size // 1024
        size_str = f"{size_kb // 1024} MB" if size_kb > 1024 else f"{size_kb} KB"

        log.info(f"Output: {output_path} ({size_str})")
        return output_path, size_str

    except subprocess.TimeoutExpired:
        log.error("Conversion timed out (>10 min)")
        return None, "Conversion timed out (file too large?)."
    except Exception as e:
        log.error(f"Conversion error: {e}")
        return None, str(e)

# ─── Input Loop ───────────────────────────────────────────────────────────────

def get_file_from_input(prompt_text):
    """Show prompt and return the trimmed input string."""
    print(prompt_text, end=" ", flush=True)
    try:
        return input().strip()
    except (EOFError, KeyboardInterrupt):
        return "q"

def run_loop():
    print(f"{GREEN}✓ FFmpeg ready! Version: {get_ffmpeg_version()}{RESET}\n")
    print(f"  Vid2Script is ready. Drag a video file into this window,")
    print(f"  or paste the full path, then press Enter.\n")
    print(f"  Type {CYAN}q{RESET} or {CYAN}quit{RESET} and press Enter to exit.\n")

    while True:
        raw = get_file_from_input(f"{BOLD}Video file:{RESET}")
        raw = raw.strip()

        if not raw:
            print(f"{YELLOW}  No input. Drag/drop a file or paste a path.{RESET}\n")
            continue

        if raw.lower() in ("q", "quit", "exit"):
            print(f"\n{GREEN}Bye!{RESET}")
            break

        input_path, err = validate_input(raw)

        if err:
            print(f"{RED}✗ {err}{RESET}\n")
            log.warning(f"Invalid input: {raw} — {err}")
            continue

        output_path, size_str = convert_to_mp3(input_path)

        if output_path:
            print(f"{GREEN}✓ Done!{RESET}  {output_path.name}  ({size_str})")
            print(f"  Saved to: {output_path}\n")
        else:
            print(f"{RED}✗ {size_str}{RESET}\n")   # size_str holds error message here

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print_banner()

    if not ffmpeg_exists():
        success = download_ffmpeg()
        if not success:
            print(f"\n{RED}FFmpeg setup failed. Please:{RESET}")
            print(f"  1. Manually download FFmpeg from: {FFMPEG_URL}")
            print(f"  2. Extract the ZIP")
            print(f"  3. Copy ffmpeg.exe into: {FFMPEG_DIR}/")
            print(f"  4. Run this script again.\n")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        version = get_ffmpeg_version()
        print(f"{GREEN}✓ FFmpeg found: {version}{RESET}\n")

    log.info("Vid2Script started")
    run_loop()
    log.info("Vid2Script closed")

if __name__ == "__main__":
    main()
