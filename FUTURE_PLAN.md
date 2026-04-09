# Vid2Script — Future Plan

## v1 — GUI .exe (current)
- [x] Tkinter GUI with Pick File + Convert buttons
- [x] Progress indicator during conversion
- [x] Output folder opens automatically on completion
- [x] Bundled FFmpeg (no PATH needed)
- [x] PyInstaller packaging → single .exe
- [x] build.bat one-click build script
- [ ] Test on Windows (pending)

## v2 — Windows .exe polish
- [ ] Add file drag-and-drop onto the window
- [ ] Show file size and duration before conversion
- [ ] Cancel button during conversion
- [ ] Remember last-used output folder

## v3 — Linux support
- [ ] Detect apt/dnf and auto-install FFmpeg via package manager
- [ ] Test on Ubuntu
- [ ] Test on Fedora

## v4 — macOS support
- [ ] Detect Homebrew and auto-install FFmpeg
- [ ] Test on Intel macOS
- [ ] Test on Apple Silicon

## v5 — Batch conversion
- [ ] Select multiple files from file picker
- [ ] Convert all in sequence with progress bar
- [ ] Show summary after batch completes

## v6 — Configurable output
- [ ] Allow user to choose bitrate (64 / 128 / 192 / 256 / 320 kbps)
- [ ] Allow user to choose output folder
- [ ] Optional WAV output
