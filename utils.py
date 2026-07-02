# utils.py
import os
import sys
import platform

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# utils.py
import os
import sys
import platform

import os
import sys
import platform


def configure_ffmpeg():
    if getattr(sys, 'frozen', False):
        # 1. Get the path to the temporary folder where PyInstaller extracted your files
        base_path = sys._MEIPASS
        bin_dir = os.path.join(base_path, "bin")

        # 2. Identify the ffmpeg file
        is_windows = platform.system() == "Windows"
        ffmpeg_exe = "ffmpeg.exe" if is_windows else "ffmpeg"
        ffmpeg_path = os.path.join(bin_dir, ffmpeg_exe)

        if os.path.exists(ffmpeg_path):
            # FIX FOR MOVIEPY: Tells it exactly where the file is
            os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path
            os.environ["FFMPEG_BINARY"] = ffmpeg_path

            # FIX FOR WHISPER: Adds the 'bin' folder to the System PATH
            # This is the "magic" that prevents [WinError 2]
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]

            print(f"--- FFmpeg initialized at {ffmpeg_path} ---")
            return True
        else:
            print(f"--- CRITICAL: FFmpeg not found at {ffmpeg_path} ---")

    return False

def get_default_font_path():
    system = platform.system()

    if system == "Windows":
        candidates = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arial.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf"),
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "tahoma.ttf"),
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return ""

    elif system == "Darwin":
        return "/Library/Fonts/Arial.ttf"

    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/arial.ttf"
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return ""


def get_whisper_model_path(model_name: str):
    filenames = {
        "tiny": "tiny.pt",
        "base": "base.pt",
        "small": "small.pt",
        "medium": "medium.pt",
        "large": "large-v3.pt",
    }

    fname = filenames.get(model_name, "base.pt")

    candidates = [
        os.path.expanduser("~/.cache/whisper"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "whisper"),
    ]

    for base in candidates:
        path = os.path.join(base, fname)
        if os.path.exists(path):
            return path

    # default expected path
    return os.path.join(candidates[0], fname)


