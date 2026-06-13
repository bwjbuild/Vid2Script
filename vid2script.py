#!/usr/bin/env python3
"""
Vid2Script - Windows-first converter for transcription workflows.
Supports:
  - YouTube URL -> MP3 (128 kbps)
  - Local video file -> MP3 (128 kbps)
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    print("ERROR: Tkinter is required.")
    sys.exit(1)

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

APP_TITLE = "Vid2Script v1.0.4"
SUPPORTED_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm",
    ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp",
}
YOUTUBE_COOKIE_BROWSER_RETRY_ORDER = (
    "edge",
    "chrome",
    "firefox",
    "brave",
    "chromium",
    "opera",
    "vivaldi",
)


def _is_probably_youtube_url(url: str) -> bool:
    lowered = (url or "").lower()
    return "youtube.com" in lowered or "youtu.be" in lowered


def _cookie_profiles_for_browser(browser: str) -> tuple[str | None, ...]:
    if browser in {"edge", "chrome", "brave", "chromium", "opera", "vivaldi"}:
        return (None, "Default", "Profile 1", "Profile 2")
    if browser == "firefox":
        return (None, "default-release", "default")
    return (None,)


def _cookie_source_label(browser: str, profile: str | None) -> str:
    if profile:
        return f"{browser.title()} ({profile})"
    return browser.title()


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return get_app_dir()


def can_write_to_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".vid2script_write_probe"
        with probe.open("w", encoding="utf-8") as fh:
            fh.write("ok")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def get_runtime_dir() -> Path:
    app_dir = get_app_dir()
    if can_write_to_dir(app_dir):
        return app_dir

    fallback = Path.home() / "Vid2ScriptData"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


APP_DIR = get_app_dir()
BUNDLE_DIR = get_bundle_dir()
RUNTIME_DIR = get_runtime_dir()
FFMPEG_DIR = BUNDLE_DIR / "ffmpeg"
FFMPEG_BIN = FFMPEG_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
FFPROBE_BIN = FFMPEG_DIR / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
OUTPUT_DIR = RUNTIME_DIR / "output"
LOG_DIR = RUNTIME_DIR / "logs"
LOG_FILE = LOG_DIR / "vid2script.log"


def ensure_runtime_dirs() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    ensure_runtime_dirs()
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(fmt)
    root.addHandler(handler)


def ffmpeg_version() -> str:
    if not FFMPEG_BIN.exists():
        return "missing"
    try:
        result = subprocess.run(
            [str(FFMPEG_BIN), "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        match = re.search(r"ffmpeg version ([^\s]+)", result.stdout)
        return match.group(1) if match else "unknown"
    except Exception:
        return "unknown"


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    idx = 1
    while True:
        candidate = parent / f"{stem}_{idx}{suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


def format_file_size(path: Path) -> str:
    size = path.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size} B"


def _looks_like_youtube_auth_challenge(error_text: str) -> bool:
    text = (error_text or "").lower()
    triggers = (
        "sign in to confirm you're not a bot",
        "sign in to confirm you’re not a bot",
        "use --cookies-from-browser",
        "use --cookies for the authentication",
        "youtube cookies",
        "use --cookies",
        "this video is unavailable",
        "http error 403",
        "http error 429",
        "too many requests",
        "unavailable videos are hidden",
    )
    return any(t in text for t in triggers)


def convert_local_video(input_path: Path, output_dir: Path, progress_callback):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = unique_output_path(output_dir / f"{input_path.stem}.mp3")

    cmd = [
        str(FFMPEG_BIN),
        "-i", str(input_path),
        "-codec:a", "libmp3lame",
        "-b:a", "128k",
        "-vn",
        "-ac", "2",
        "-y",
        str(output_path),
    ]

    logging.info("Starting local conversion: %s", input_path)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    while proc.poll() is None:
        progress_callback("Converting local file to MP3...")
        time.sleep(1.2)

    stderr_tail = ""
    if proc.stderr:
        stderr_tail = proc.stderr.read()[-1200:]

    if proc.returncode != 0:
        logging.error("FFmpeg failed for %s: %s", input_path, stderr_tail)
        return False, f"FFmpeg failed:\n{stderr_tail}", None

    if not output_path.exists():
        logging.error("Output file was not created for %s", input_path)
        return False, "Output MP3 was not created.", None

    logging.info("Local conversion finished: %s", output_path)
    return True, f"Created {output_path.name} ({format_file_size(output_path)})", output_path


def convert_youtube_url(url: str, output_dir: Path, progress_callback):
    if yt_dlp is None:
        return False, "yt-dlp is not available inside this build.", None

    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.time()

    def hook(data):
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes")
            if total and downloaded:
                pct = max(0.0, min(100.0, (downloaded / total) * 100.0))
                progress_callback(f"Downloading audio... {pct:.1f}%")
            else:
                progress_callback("Downloading audio...")
        elif status == "finished":
            progress_callback("Download complete. Converting to 128 kbps MP3...")

    def build_opts(cookie_source: tuple | None = None) -> dict:
        opts = {
            "format": "bestaudio*",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "overwrites": True,
            "windowsfilenames": True,
            "ffmpeg_location": str(FFMPEG_DIR),
            "paths": {"home": str(output_dir)},
            "outtmpl": {"default": "%(title).180B [%(id)s].%(ext)s"},
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "128",
                }
            ],
            "postprocessor_args": ["-ac", "2"],
            "progress_hooks": [hook],
            "cachedir": False,
            "extractor_retries": 3,
            "file_access_retries": 3,
            # Use web + ios clients (android triggers anti-bot more aggressively in 2026).
            "extractor_args": {"youtube": {"player_client": ["web", "ios"]}},
        }
        if cookie_source:
            opts["cookiesfrombrowser"] = cookie_source
        return opts

    logging.info("Starting YouTube conversion: %s", url)

    def run_download(ydl_opts: dict) -> Path | None:
        # Snapshot existing mp3s before download so we can detect the actual
        # post-processed file, instead of guessing from prepare_filename().
        before = set(output_dir.glob("*.mp3")) if output_dir.exists() else set()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            new_mp3s = set(output_dir.glob("*.mp3")) - before
            if new_mp3s:
                return max(new_mp3s, key=lambda p: p.stat().st_mtime)
        return None

    try:
        candidate = run_download(build_opts())
        if candidate and candidate.exists():
            logging.info("YouTube conversion finished: %s", candidate)
            return True, f"Created {candidate.name} ({format_file_size(candidate)})", candidate
    except Exception as exc:
        error_text = str(exc)
        should_try_cookie_retry = _looks_like_youtube_auth_challenge(error_text)
        if not should_try_cookie_retry:
            logging.exception("YouTube conversion failed for %s", url)
            return False, f"Download failed:\n{exc}", None

        logging.warning(
            "YouTube download failed. Retrying with browser cookies. Initial error: %s",
            error_text,
        )
        progress_callback("YouTube requested verification. Retrying with browser cookies and profiles...")

        last_cookie_error = error_text
        for browser in YOUTUBE_COOKIE_BROWSER_RETRY_ORDER:
            for profile in _cookie_profiles_for_browser(browser):
                label = _cookie_source_label(browser, profile)
                cookie_source = (browser,) if profile is None else (browser, profile)
                try:
                    progress_callback(f"Retrying with {label} cookies...")
                    candidate = run_download(build_opts(cookie_source=cookie_source))
                    if candidate and candidate.exists():
                        logging.info(
                            "YouTube conversion finished with %s cookies: %s",
                            label,
                            candidate,
                        )
                        return True, f"Created {candidate.name} ({format_file_size(candidate)})", candidate
                except Exception as browser_exc:
                    last_cookie_error = str(browser_exc)
                    logging.warning(
                        "YouTube retry with %s cookies failed: %s",
                        label,
                        last_cookie_error,
                    )

        help_text = (
            "YouTube asked for sign-in verification and automatic browser-cookie retry failed.\n\n"
            "Fix:\n"
            "1. Open YouTube in Edge or Chrome\n"
            "2. Sign in and play the target video once\n"
            "3. Retry in Vid2Script\n\n"
            f"Last error:\n{last_cookie_error}"
        )
        return False, help_text, None

    recent_mp3s = sorted(
        output_dir.glob("*.mp3"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for mp3 in recent_mp3s:
        if mp3.stat().st_mtime >= started_at - 5:
            logging.info("YouTube conversion finished (fallback path): %s", mp3)
            return True, f"Created {mp3.name} ({format_file_size(mp3)})", mp3

    logging.error("YouTube conversion completed but output file could not be located")
    return False, "Conversion completed but output MP3 could not be located.", None


class Vid2ScriptApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_TITLE} - 128 kbps MP3")
        self.root.resizable(False, False)
        self.root.configure(bg="#18212b")

        self.selected_file: Path | None = None
        self.converting = False

        self.source_mode = tk.StringVar(value="url")
        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(OUTPUT_DIR))

        self._build_ui()
        self._center_window(700, 430)
        self._wire_events()
        self._run_startup_checks()
        self._refresh_mode()
        self._refresh_convert_button()

    def _center_window(self, width: int, height: int) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self) -> None:
        bg = "#18212b"
        card = "#243342"
        text = "#e8edf2"
        muted = "#a9b6c2"
        accent = "#1e88e5"
        accent_hover = "#1976d2"
        success = "#43a047"
        warn = "#f9a825"
        err = "#e53935"

        self.colors = {
            "text": text,
            "muted": muted,
            "success": success,
            "warn": warn,
            "err": err,
            "accent": accent,
        }

        title = tk.Label(
            self.root,
            text="Vid2Script",
            font=("Segoe UI", 22, "bold"),
            fg=text,
            bg=bg,
        )
        title.pack(pady=(16, 2))

        subtitle = tk.Label(
            self.root,
            text="YouTube or local video to MP3 (128 kbps) for transcription",
            font=("Segoe UI", 10),
            fg=muted,
            bg=bg,
        )
        subtitle.pack(pady=(0, 12))

        panel = tk.Frame(self.root, bg=card, padx=16, pady=14)
        panel.pack(fill="x", padx=22)

        mode_row = tk.Frame(panel, bg=card)
        mode_row.pack(fill="x")

        tk.Label(mode_row, text="Input", font=("Segoe UI", 10, "bold"), fg=text, bg=card).pack(side="left")

        tk.Radiobutton(
            mode_row,
            text="YouTube URL",
            variable=self.source_mode,
            value="url",
            bg=card,
            fg=text,
            selectcolor=card,
            activebackground=card,
            activeforeground=text,
            font=("Segoe UI", 9),
            command=self._refresh_mode,
        ).pack(side="left", padx=(14, 4))

        tk.Radiobutton(
            mode_row,
            text="Local file",
            variable=self.source_mode,
            value="file",
            bg=card,
            fg=text,
            selectcolor=card,
            activebackground=card,
            activeforeground=text,
            font=("Segoe UI", 9),
            command=self._refresh_mode,
        ).pack(side="left", padx=(10, 0))

        url_row = tk.Frame(panel, bg=card)
        url_row.pack(fill="x", pady=(12, 0))
        tk.Label(url_row, text="URL", width=11, anchor="w", fg=muted, bg=card, font=("Segoe UI", 9)).pack(side="left")
        self.url_entry = tk.Entry(url_row, textvariable=self.url_var, font=("Segoe UI", 10), width=62)
        self.url_entry.pack(side="left", fill="x", expand=True)

        file_row = tk.Frame(panel, bg=card)
        file_row.pack(fill="x", pady=(10, 0))
        tk.Label(file_row, text="File", width=11, anchor="w", fg=muted, bg=card, font=("Segoe UI", 9)).pack(side="left")

        self.file_display = tk.Label(
            file_row,
            text="No file selected",
            font=("Segoe UI", 9),
            fg=muted,
            bg=card,
            anchor="w",
            width=54,
        )
        self.file_display.pack(side="left", padx=(0, 8))

        self.pick_btn = tk.Button(
            file_row,
            text="Pick File",
            bg=accent,
            fg="white",
            activebackground=accent_hover,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            command=self._pick_file,
            cursor="hand2",
        )
        self.pick_btn.pack(side="left")

        out_row = tk.Frame(panel, bg=card)
        out_row.pack(fill="x", pady=(10, 0))
        tk.Label(out_row, text="Output", width=11, anchor="w", fg=muted, bg=card, font=("Segoe UI", 9)).pack(side="left")

        self.out_entry = tk.Entry(out_row, textvariable=self.output_var, font=("Segoe UI", 10), width=52)
        self.out_entry.pack(side="left", fill="x", expand=True)

        self.out_btn = tk.Button(
            out_row,
            text="Browse",
            bg="#455a64",
            fg="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            command=self._pick_output_dir,
            cursor="hand2",
        )
        self.out_btn.pack(side="left", padx=(8, 0))

        action_row = tk.Frame(self.root, bg=bg)
        action_row.pack(fill="x", padx=22, pady=(12, 0))

        self.convert_btn = tk.Button(
            action_row,
            text="Convert to 128 kbps MP3",
            font=("Segoe UI", 10, "bold"),
            bg=accent,
            fg="white",
            activebackground=accent_hover,
            relief="flat",
            padx=16,
            pady=8,
            command=self._start_convert,
            cursor="hand2",
        )
        self.convert_btn.pack(side="left")

        self.open_output_btn = tk.Button(
            action_row,
            text="Open Output Folder",
            font=("Segoe UI", 9, "bold"),
            bg="#455a64",
            fg="white",
            relief="flat",
            padx=14,
            pady=8,
            command=lambda: self._open_folder(Path(self.output_var.get().strip() or OUTPUT_DIR)),
            cursor="hand2",
        )
        self.open_output_btn.pack(side="left", padx=(10, 0))

        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 9),
            fg=warn,
            bg=bg,
            wraplength=650,
            justify="left",
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=22, pady=(12, 0))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Vid2Script.Horizontal.TProgressbar",
            troughcolor="#243342",
            background=accent,
            thickness=7,
        )

        self.progress = ttk.Progressbar(
            self.root,
            mode="indeterminate",
            length=650,
            style="Vid2Script.Horizontal.TProgressbar",
        )
        self.progress.pack(fill="x", padx=22, pady=(8, 0))

    def _wire_events(self) -> None:
        self.url_var.trace_add("write", lambda *_: self._refresh_convert_button())
        self.output_var.trace_add("write", lambda *_: self._refresh_convert_button())

    def _run_startup_checks(self) -> None:
        missing = []
        if not FFMPEG_BIN.exists():
            missing.append(f"Missing FFmpeg: {FFMPEG_BIN}")
        if not FFPROBE_BIN.exists():
            missing.append(f"Missing FFprobe: {FFPROBE_BIN}")
        if yt_dlp is None:
            missing.append("Missing yt-dlp module in this build")

        if missing:
            msg = "Startup check failed:\n- " + "\n- ".join(missing)
            self._set_status(msg, "err")
            logging.error(msg)
            messagebox.showerror(
                APP_TITLE,
                f"Required components are missing.\n\n{msg}\n\nSee log file:\n{LOG_FILE}",
            )
            return

        version = ffmpeg_version()
        self._set_status(f"Ready. FFmpeg {version} detected.", "success")

    def _set_status(self, text: str, level: str = "warn") -> None:
        color = self.colors.get(level, self.colors["warn"])
        self.status_label.config(text=text, fg=color)

    def _refresh_mode(self) -> None:
        mode = self.source_mode.get()
        if mode == "url":
            self.url_entry.config(state="normal")
            self.pick_btn.config(state="disabled", cursor="arrow", bg="#4d5d6c")
            self.file_display.config(fg=self.colors["muted"])
            self.url_entry.focus_set()
        else:
            self.url_entry.config(state="disabled")
            self.pick_btn.config(state="normal", cursor="hand2", bg=self.colors["accent"])
            self.file_display.config(fg=self.colors["text"] if self.selected_file else self.colors["muted"])
        self._refresh_convert_button()

    def _refresh_convert_button(self) -> None:
        if self.converting:
            self.convert_btn.config(state="disabled", bg="#4d5d6c", cursor="arrow")
            return

        output_ok = bool(self.output_var.get().strip())
        mode = self.source_mode.get()
        source_ok = False

        if mode == "url":
            source_ok = bool(self.url_var.get().strip())
        elif mode == "file":
            source_ok = self.selected_file is not None

        ready = output_ok and source_ok and FFMPEG_BIN.exists() and yt_dlp is not None
        if ready:
            self.convert_btn.config(state="normal", bg=self.colors["accent"], cursor="hand2")
        else:
            self.convert_btn.config(state="disabled", bg="#4d5d6c", cursor="arrow")

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=[
                ("Video files", "*.mp4 *.mkv *.avi *.mov *.webm *.wmv *.flv *.m4v *.mpg *.mpeg *.3gp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        p = Path(path)
        if p.suffix.lower() not in SUPPORTED_EXTS:
            messagebox.showerror(
                "Unsupported format",
                f"{p.suffix} is not supported.\n\nSupported: {', '.join(sorted(SUPPORTED_EXTS))}",
            )
            return

        self.selected_file = p
        display_name = p.name if len(p.name) <= 58 else p.name[:55] + "..."
        self.file_display.config(text=display_name, fg=self.colors["text"])
        self._set_status(f"Selected file: {p}", "warn")
        self._refresh_convert_button()

    def _pick_output_dir(self) -> None:
        current = self.output_var.get().strip() or str(OUTPUT_DIR)
        path = filedialog.askdirectory(title="Select output folder", initialdir=current)
        if not path:
            return
        self.output_var.set(path)
        self._refresh_convert_button()

    def _start_convert(self) -> None:
        if self.converting:
            return

        if not FFMPEG_BIN.exists():
            messagebox.showerror(APP_TITLE, f"FFmpeg is missing:\n{FFMPEG_BIN}")
            return

        if yt_dlp is None:
            messagebox.showerror(APP_TITLE, "yt-dlp is missing in this build.")
            return

        output_text = self.output_var.get().strip()
        if not output_text:
            messagebox.showerror(APP_TITLE, "Please choose an output folder.")
            return

        output_dir = Path(output_text)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Cannot use output folder:\n{exc}")
            return

        mode = self.source_mode.get()
        if mode == "url":
            source = self.url_var.get().strip()
            if not source:
                messagebox.showerror(APP_TITLE, "Please paste a YouTube URL.")
                return
            if not (source.startswith("http://") or source.startswith("https://")):
                messagebox.showerror(APP_TITLE, "URL must start with http:// or https://")
                return
        else:
            if not self.selected_file:
                messagebox.showerror(APP_TITLE, "Please pick a local video file.")
                return
            if not self.selected_file.exists():
                messagebox.showerror(APP_TITLE, "Selected file no longer exists.")
                return
            source = str(self.selected_file)

        self.converting = True
        self._refresh_convert_button()
        self.progress.start(10)
        self._set_status("Working...", "warn")

        thread = threading.Thread(
            target=self._run_convert,
            args=(mode, source, output_dir),
            daemon=True,
        )
        thread.start()

    def _run_convert(self, mode: str, source: str, output_dir: Path) -> None:
        def status_cb(text: str) -> None:
            self.root.after(0, lambda: self._set_status(text, "warn"))

        if mode == "url":
            success, msg, out_path = convert_youtube_url(source, output_dir, status_cb)
        else:
            success, msg, out_path = convert_local_video(Path(source), output_dir, status_cb)

        self.root.after(0, lambda: self._finish_convert(success, msg, out_path, output_dir))

    def _finish_convert(self, success: bool, msg: str, out_path: Path | None, output_dir: Path) -> None:
        self.progress.stop()
        self.converting = False
        self._refresh_convert_button()

        if success:
            self._set_status(msg, "success")
            self._open_folder(output_dir)
            messagebox.showinfo(APP_TITLE, f"Done.\n\n{msg}\n\nSaved in:\n{output_dir}")
            logging.info("Conversion succeeded: %s", out_path)
            if self.source_mode.get() == "file":
                self.selected_file = None
                self.file_display.config(text="No file selected", fg=self.colors["muted"])
        else:
            self._set_status("Conversion failed. See log file for details.", "err")
            messagebox.showerror(APP_TITLE, msg)
            logging.error("Conversion failed: %s", msg)

    def _open_folder(self, path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            logging.warning("Failed to open folder %s: %s", path, exc)


def main() -> None:
    ensure_runtime_dirs()
    configure_logging()
    logging.info("App start. app_dir=%s bundle_dir=%s runtime_dir=%s", APP_DIR, BUNDLE_DIR, RUNTIME_DIR)

    root = tk.Tk()
    Vid2ScriptApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
