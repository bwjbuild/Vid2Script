# Vid2Script

**Video → MP3 converter. Drag a file, get a 128 kbps MP3.**

[View on GitHub](https://github.com/bwjbuild/Vid2Script)

Part of the Vid2Script transcript generation pipeline: video file → MP3 audio → transcription.

## First-Time Setup

**Double-click `SETUP.bat`** inside this folder. It will automatically download and set up:
- Python 3.12 (Embeddable) → `python/` folder
- FFmpeg static binary → `ffmpeg/` folder

This takes a few minutes on first run. Run it once, done forever.

## Quick Start

1. **Double-click `vid2script.bat`** — a terminal window opens
2. **Drag a video file** into the terminal and press Enter, or paste the file path
3. Your MP3 appears in the `output/` folder

Type `q` and press Enter to quit.

## File Structure

```
Vid2Script/
├── vid2script.bat      ← double-click to run
├── SETUP.bat           ← first-time setup (run once)
├── vid2script.py       ← main script
├── python/             ← bundled Python (auto-installed)
│   └── python.exe
├── ffmpeg/             ← bundled FFmpeg (auto-installed)
│   └── ffmpeg.exe
├── output/             ← converted MP3s land here
└── logs/               ← conversion logs
```

## Supported Formats

.mp4, .mkv, .avi, .mov, .webm, .wmv, .flv, .m4v, .mpg, .mpeg, .3gp

## Output

- Format: MP3
- Bitrate: 128 kbps
- Channels: Stereo
- Location: `output/` folder inside Vid2Script/

## How It Works

Uses FFmpeg under the hood:

```
ffmpeg -i input.mp4 -codec:a libmp3lame -b:a 128k -vn output.mp3
```

- `-codec:a libmp3lame` — MP3 encoding via LAME
- `-b:a 128k` — 128 kbps bitrate
- `-vn` — strips the video stream, audio only

## Troubleshooting

### "Vid2Script requires Python but it was not found"
Run `SETUP.bat` first. It downloads Python and FFmpeg automatically.

### FFmpeg / Python download is slow or fails
1. Run `SETUP.bat` again — it will resume
2. If it keeps failing, manually download:
   - **Python**: https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip
   - **FFmpeg**: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
3. Extract Python to the `python/` folder, FFmpeg to the `ffmpeg/` folder
4. Run `vid2script.bat`

### "File not found" error
Make sure the file path you pasted is complete, including the extension. On Windows, paths look like: `C:\Users\YourName\Videos\file.mp4`

### FFmpeg download fails
1. Manually download from: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip)
2. Extract the ZIP
3. Copy `ffmpeg.exe` into the `ffmpeg/` folder inside Vid2Script
4. Run `python vid2script.py` again

### Very large file times out
The default timeout is 10 minutes per conversion. For hour-long videos, this should be enough. If needed, increase the `timeout=600` value in `vid2script.py`.

## Future Additions

- Linux support
- macOS support
- Batch conversion (convert multiple files at once)
- Configurable bitrate output
- GUI wrapper

See `FUTURE_PLAN.md` for full roadmap.
