# Vid2Script

Windows-first converter for transcription pipelines.

- Input: YouTube URL or local video file
- Output: MP3 at 128 kbps stereo
- UX goal: paste/click once, get MP3

## Download (Recommended)

- Latest release page: https://github.com/bwjbuild/Vid2Script/releases/latest
- `v1.0.2` page: https://github.com/bwjbuild/Vid2Script/releases/tag/v1.0.2
- Direct EXE (`v1.0.2`): https://github.com/bwjbuild/Vid2Script/releases/download/v1.0.2/Vid2Script.exe
- SHA256 (`Vid2Script.exe`): `3f631c649b38b85a60bc04fb0e0dfbf23e8596796a5e91f1d63237feb41c66bb`

## What Was Fixed

This version addresses the previous Windows packaging issue (`failed to load python dll`) by switching to a **single-file PyInstaller build**.

- End users now receive one file: `Vid2Script.exe`
- No Python installation is required on user machines
- No dependency on users copying an entire `dist\Vid2Script\` folder
- For YouTube anti-bot challenges, the app now retries using local browser cookies automatically

## End-User Usage (Windows)

1. Open `Vid2Script.exe`
2. Choose one input mode:
   - Paste a YouTube URL, or
   - Pick a local video file
3. Click **Convert to 128 kbps MP3**
4. MP3 is saved in `output/` (or your chosen output folder) and the folder opens automatically

## Build Without Windows (GitHub Actions)

If you do not have a Windows machine, use the included CI workflow:

1. Push this repo to GitHub
2. Open **Actions** -> **Build Windows EXE**
3. Click **Run workflow**
4. After it finishes, download artifact: `Vid2Script-windows-exe`
5. Inside it, you get `Vid2Script.exe` ready to share

## Build (for You)

### Prerequisites

- Windows 10/11 (64-bit)
- Python 3.10+
- Internet connection (for dependency + FFmpeg download)

### One-command build

```bat
build.bat
```

`build.bat` automatically:

1. Runs `SETUP.bat` to download FFmpeg (`ffmpeg.exe` + `ffprobe.exe`)
2. Creates `.venv-build`
3. Installs `yt-dlp` and `pyinstaller`
4. Builds a single-file executable

Build output:

```text
dist\Vid2Script.exe
```

## Source Layout

```text
vid2script.py          # GUI + conversion logic
vid2script.spec        # PyInstaller one-file spec
SETUP.bat              # Downloads FFmpeg + prepares runtime dirs
build.bat              # Full Windows build pipeline
requirements.txt       # Runtime Python deps
requirements-build.txt # Build deps
```

## Notes

- YouTube downloads depend on `yt-dlp` extractor behavior and site-side changes.
- Use only content you are authorized to download and process.
- Runtime logs are written to `logs/vid2script.log`.
- If the EXE folder is not writable, the app falls back to `~/Vid2ScriptData/`.

## Troubleshooting

### 1) EXE does not start

- Run from `cmd` to inspect behavior:
  ```bat
  dist\Vid2Script.exe
  ```
- Check `logs/vid2script.log` near the EXE location.

### 2) YouTube conversion fails

- If you see `Sign in to confirm you're not a bot`, open YouTube in your browser first (while signed in), then retry in Vid2Script.
- Vid2Script auto-retries with cookies from common browsers (`Edge`, `Chrome`, `Firefox`, `Brave`, `Chromium`, `Opera`, `Vivaldi`).
- If it still fails, download the newest EXE from releases (contains latest bundled `yt-dlp`).

### 3) FFmpeg missing message in app

- Re-run:
  ```bat
  SETUP.bat
  ```

### 4) Build failed

- Confirm Python 3.10+ is installed and available via `py` or `python`
- Re-run `build.bat` and review terminal errors
