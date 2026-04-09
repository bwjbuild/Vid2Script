# Vid2Script — Future Plan

## v1 — Current (Windows, drag-and-drop, 128 kbps MP3)
- FFmpeg auto-download on first run
- Drag-and-drop or paste path input
- Fixed 128 kbps output
- Logging

## v1.1 — Windows polish
- [x] Add a `vid2script.bat` launcher (double-click to run, no terminal needed)
- [ ] Better error messages for corrupt video files
- [ ] Show progress bar during conversion using FFmpeg progress output

## v2 — Linux support
- [ ] Detect apt/yum/dnf and auto-install FFmpeg via package manager
- [ ] Test on Ubuntu/Debian
- [ ] Test on Fedora/RHEL
- [ ] Update README with Linux install instructions

## v3 — macOS support
- [ ] Detect Homebrew and auto-install FFmpeg
- [ ] Test on Intel macOS
- [ ] Test on Apple Silicon (arm64)
- [ ] Update README with macOS install instructions

## v4 — Batch conversion
- [ ] `python vid2script.py --batch` flag
- [ ] Select multiple files from file picker
- [ ] Convert all in sequence with progress indicator

## v5 — Configurable output
- [ ] Allow user to choose bitrate (64 / 128 / 192 / 256 / 320 kbps)
- [ ] Allow user to choose output folder (not just output/)
- [ ] Optional: WAV output for highest quality

## v6 — GUI wrapper
- [ ] Add a simple PySimpleGUI drag-and-drop window
- [ ] Show file name, duration estimate, progress bar
- [ ] Single-file .exe build with PyInstaller
