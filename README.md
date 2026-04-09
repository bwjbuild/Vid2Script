# Vid2Script

**Video → MP3 converter. Pick a file, click Convert, get your MP3.**

[View on GitHub](https://github.com/bwjbuild/Vid2Script)

---

## For Users — Get Started in 2 Steps

### Step 1 — Build the .exe (one-time)

On Windows, run these two batch files in order:

```bash
# Run once: downloads Python + FFmpeg (~5 minutes)
SETUP.bat

# Run once: builds the .exe (~2 minutes)
build.bat
```

That's it. After `build.bat` finishes, your `.exe` is ready.

### Step 2 — Use It (forever)

1. Open `dist\Vid2Script\Vid2Script.exe`
2. Click **"Pick File"** — select any video file
3. Click **"Convert"** — wait a few seconds
4. Done! The output folder opens automatically — your MP3 is there

No terminal. No typing. No setup needed after the first build.

---

## System Requirements

- **Windows 10 or 11** (64-bit)
- No Python installation required after building

---

## File Structure (Development)

```
Vid2Script/
├── vid2script.py       ← main GUI script (Tkinter)
├── vid2script.spec     ← PyInstaller build config
├── SETUP.bat           ← download Python + FFmpeg
├── build.bat           ← build .exe
├── ffmpeg/             ← FFmpeg binary (from SETUP.bat)
├── output/             ← converted MP3s
└── logs/               ← conversion logs
```

After `build.bat`:
```
dist/
└── Vid2Script/
    ├── Vid2Script.exe  ← THE .exe — share this folder
    ├── ffmpeg/
    └── output/
```

---

## Build Instructions (for contributors)

### Prerequisites
- Windows 10/11
- Python 3.7+ (only needed on the build machine, not on end-user machines)

### Build Steps

1. Clone / download the repo
2. Run `SETUP.bat` — downloads FFmpeg
3. Run `build.bat` — builds the `.exe`
4. Share the `dist\Vid2Script\` folder

### Output

The build produces a complete folder at `dist\Vid2Script/` containing:
- `Vid2Script.exe` — the single-file app
- `ffmpeg/` — bundled FFmpeg binary
- `output/` — empty folder, created at runtime

End users only need this folder. No installation. No Python required.

---

## Supported Formats

.mp4, .mkv, .avi, .mov, .webm, .wmv, .flv, .m4v, .mpg, .mpeg, .3gp

## Output

- Format: MP3
- Bitrate: 128 kbps
- Channels: Stereo
- Location: `output/` folder (opens automatically after conversion)

---

## Troubleshooting

### FFmpeg not found after running SETUP.bat
1. Verify `ffmpeg/ffmpeg.exe` exists in the Vid2Script folder
2. Re-run `SETUP.bat`
3. If it keeps failing: manually download from https://www.gyan.dev/ffmpeg/builds/ and extract `ffmpeg.exe` to `ffmpeg/`

### "Build failed" error
1. Make sure you ran `SETUP.bat` before `build.bat`
2. Make sure you have an active internet connection
3. Try running `pip install pyinstaller` manually in a terminal, then re-run `build.bat`

### .exe doesn't open
1. Windows Defender may block it on first run — click "More info" → "Run anyway"
2. Make sure SmartScreen is not blocking the file
3. Try running as Administrator

### The file picker shows no files
The file picker filters by video extensions. Make sure you're selecting a video file (.mp4, .mkv, etc.)

---

## How It Works

```
ffmpeg -i input.mp4 -codec:a libmp3lame -b:a 128k -vn output.mp3
```

- `-codec:a libmp3lame` — MP3 encoding via LAME
- `-b:a 128k` — 128 kbps bitrate
- `-vn` — strips the video stream, audio only

---

## Future Additions

- Linux support
- macOS support
- Batch conversion (multiple files at once)
- Configurable bitrate
- Drag-and-drop onto the window

See `FUTURE_PLAN.md` for full roadmap.
