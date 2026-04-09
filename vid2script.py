#!/usr/bin/env python3
"""
Vid2Script — Video to MP3 Converter (GUI)
A simple GUI for converting video files to MP3 (128 kbps) using FFmpeg.
Packaged as a standalone .exe with PyInstaller.
"""

import os
import sys
import subprocess
import threading
import re
from pathlib import Path

# ─── Tkinter (built into Python — no extra deps) ───────────────────────────────
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    # Fallback if Tkinter is somehow missing (should never happen on Windows)
    print("ERROR: Tkinter is not available. Please install Python with tkinter support.")
    sys.exit(1)


# ─── Resource Paths ────────────────────────────────────────────────────────────

def get_resource_path(relative_path: str) -> Path:
    """
    Resolves a path to the bundled resource.
    Works both:
      - In development (script folder)
      - After PyInstaller packaging (next to the .exe)
    """
    if getattr(sys, "frozen", False):
        # Running as bundled .exe — resources are next to the .exe
        base = Path(sys.executable).parent
    else:
        # Running as .py script
        base = Path(__file__).parent.resolve()

    return base / relative_path


SCRIPT_DIR   = get_resource_path(".")
FFMPEG_BIN   = get_resource_path("ffmpeg/ffmpeg.exe")
OUTPUT_DIR   = get_resource_path("output")
LOG_DIR      = get_resource_path("logs")

SUPPORTED_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm",
    ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".3gp"
}


# ─── FFmpeg Check ─────────────────────────────────────────────────────────────

def check_ffmpeg() -> tuple[bool, str]:
    """Check if FFmpeg binary exists and get version."""
    if not FFMPEG_BIN.exists():
        return False, "FFmpeg not found"
    try:
        result = subprocess.run(
            [str(FFMPEG_BIN), "-version"],
            capture_output=True, text=True, timeout=10
        )
        match = re.search(r"ffmpeg version ([^\s]+)", result.stdout)
        version = match.group(1) if match else "unknown"
        return True, version
    except Exception:
        return False, "Error checking FFmpeg"


# ─── Conversion ───────────────────────────────────────────────────────────────

def convert_to_mp3(input_path: Path, progress_callback):
    """
    Convert a video file to MP3 (128 kbps).
    Calls progress_callback(text) to report status.
    Returns (success, output_path_or_error_message).
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_name = input_path.stem + ".mp3"
    output_path = OUTPUT_DIR / output_name

    cmd = [
        str(FFMPEG_BIN),
        "-i",       str(input_path),
        "-codec:a", "libmp3lame",
        "-b:a",     "128k",
        "-vn",
        "-y",
        str(output_path),
    ]

    def run_progress():
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Poll and update progress
            while proc.poll() is None:
                progress_callback(f"Converting...")
                import time
                time.sleep(1.5)

            returncode = proc.poll()

            if returncode != 0:
                stderr = proc.stderr.read()[-500:]
                return False, f"FFmpeg failed:\n{stderr}"

            if not output_path.exists():
                return False, "Output file was not created."

            size_kb = output_path.stat().st_size // 1024
            size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb} KB"
            return True, size_str

        except Exception as e:
            return False, str(e)

    return run_progress()


# ─── GUI App ─────────────────────────────────────────────────────────────────

class Vid2ScriptApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vid2Script — Video to MP3")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        # Center window
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 560, 360
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

        self.selected_file = None
        self.converting = False

        self._build_ui()

        # Check FFmpeg on startup
        self._check_ffmpeg_on_startup()

    # ── UI Builder ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        bg   = "#1e1e2e"
        card = "#2a2a3e"
        accent = "#7c6af7"
        accent_h = "#6a59d6"
        text   = "#e0e0e0"
        sub    = "#9090a0"
        green  = "#6ad46a"
        red    = "#f07070"
        yellow = "#f0c060"

        # Title
        title = tk.Label(
            self.root, text="Vid2Script",
            font=("Segoe UI", 22, "bold"),
            fg=text, bg=bg
        )
        title.pack(pady=(18, 2))

        subtitle = tk.Label(
            self.root, text="Video → MP3 (128 kbps)",
            font=("Segoe UI", 10),
            fg=sub, bg=bg
        )
        subtitle.pack(pady=(0, 14))

        # File card
        card_frame = tk.Frame(self.root, bg=card, padx=16, pady=14)
        card_frame.pack(fill="x", padx=24)

        self.file_label = tk.Label(
            card_frame, text="No file selected",
            font=("Segoe UI", 10),
            fg=sub, bg=card, wraplength=420, justify="left", anchor="w"
        )
        self.file_label.pack(fill="x")

        btn_row = tk.Frame(card_frame, bg=card)
        btn_row.pack(fill="x", pady=(10, 0))

        pick_btn = tk.Button(
            btn_row, text="Pick File",
            font=("Segoe UI", 10, "bold"),
            bg=accent, fg="white", activebackground=accent_h,
            relief="flat", padx=14, pady=5,
            cursor="hand2", command=self._pick_file
        )
        pick_btn.pack(side="left")

        self.convert_btn = tk.Button(
            btn_row, text="Convert",
            font=("Segoe UI", 10, "bold"),
            bg="#44445a", fg="#808090",
            relief="flat", padx=18, pady=5,
            state="disabled", cursor="not_allowed",
            command=self._start_convert
        )
        self.convert_btn.pack(side="right")

        # Status area
        self.status_label = tk.Label(
            self.root, text="",
            font=("Segoe UI", 9),
            fg=yellow, bg=bg, wraplength=500, justify="center"
        )
        self.status_label.pack(pady=(12, 0))

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root, mode="indeterminate",
            length=500, style="Vid2Script.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=(6, 0))

        # Style for progress bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Vid2Script.Horizontal.TProgressbar",
            troughcolor=card, background=accent,
            thickness=6
        )

    # ── FFmpeg Check ────────────────────────────────────────────────────────────

    def _check_ffmpeg_on_startup(self):
        ok, msg = check_ffmpeg()
        if ok:
            self.status_label.config(text=f"FFmpeg ready ({msg})", fg="#6ad46a")
        else:
            self.status_label.config(
                text=f"FFmpeg missing: {msg}\n\n"
                     "Please run SETUP.bat first to download FFmpeg.",
                fg="#f07070"
            )

    # ── File Picker ────────────────────────────────────────────────────────────

    def _pick_file(self):
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
                f"'{p.suffix}' is not supported.\n\n"
                f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}"
            )
            return

        self.selected_file = p
        short = p.name if len(p.name) <= 40 else p.name[:37] + "..."
        self.file_label.config(text=short, fg="#e0e0e0")

        self.convert_btn.config(
            state="normal", bg="#7c6af7", fg="white",
            activebackground="#6a59d6", cursor="hand2"
        )
        self.status_label.config(text="", fg="#9090a0")

    # ── Convert ────────────────────────────────────────────────────────────────

    def _start_convert(self):
        if not self.selected_file or self.converting:
            return

        self.converting = True
        self.convert_btn.config(state="disabled", bg="#44445a", fg="#808090", cursor="not_allowed")
        self.status_label.config(text="Converting... please wait.", fg="#f0c060")
        self.progress.start(10)

        thread = threading.Thread(target=self._run_convert, daemon=True)
        thread.start()

    def _run_convert(self):
        input_path = self.selected_file
        success, result = convert_to_mp3(input_path, self._update_status_from_thread)

        self.root.after(0, self._conversion_done, success, result)

    def _update_status_from_thread(self, text):
        """Called from conversion thread — schedule GUI update on main thread."""
        self.root.after(0, lambda t=text: self.status_label.config(text=t, fg="#f0c060"))

    def _conversion_done(self, success, result):
        self.progress.stop()
        self.converting = False

        if success:
            self.status_label.config(
                text=f"Done! ({result})",
                fg="#6ad46a"
            )
            self.convert_btn.config(
                state="normal", bg="#6ad46a", fg="white",
                activebackground="#5ac055", cursor="hand2"
            )
            # Open output folder
            self._open_output_folder()
            messagebox.showinfo(
                "Conversion complete",
                f"MP3 saved to:\n{OUTPUT_DIR}"
            )
            # Reset UI for next file
            self.selected_file = None
            self.file_label.config(text="No file selected", fg="#9090a0")
            self.convert_btn.config(
                state="disabled", bg="#44445a", fg="#808090",
                cursor="not_allowed"
            )
            self.status_label.config(text="FFmpeg ready", fg="#6ad46a")
        else:
            self.status_label.config(text="Error!", fg="#f07070")
            messagebox.showerror("Conversion failed", result)
            self.convert_btn.config(
                state="normal", bg="#7c6af7", fg="white",
                activebackground="#6a59d6", cursor="hand2"
            )

    def _open_output_folder(self):
        """Open the output folder in Windows Explorer."""
        try:
            os.startfile(str(OUTPUT_DIR))
        except AttributeError:
            # Not on Windows — try xdg-open on Linux
            try:
                subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
            except Exception:
                pass


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Ensure output/log dirs exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = tk.Tk()
    app = Vid2ScriptApp(root)
    root.mainloop()
