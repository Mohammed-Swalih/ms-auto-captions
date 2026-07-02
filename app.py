# app.py

import sys
import  subprocess

if sys.platform == "win32":
    # We "override" the internal subprocess call
    # to always include the 'No Window' flag
    _old_popen = subprocess.Popen


    class PopenHide(_old_popen):
        def __init__(self, *args, **kwargs):
            # 0x08000000 is the Windows constant for CREATE_NO_WINDOW
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | 0x08000000
            super().__init__(*args, **kwargs)


    # Inject our modified version back into the system
    subprocess.Popen = PopenHide
import os
app_data_dir = os.path.join(os.environ["LOCALAPPDATA"], "MSAutoCaptions")

# 2. Create it if it doesn't exist
if not os.path.exists(app_data_dir):
    os.makedirs(app_data_dir, exist_ok=True)

# 3. CRITICAL: Move the app's focus to this safe folder
# This ensures MoviePy's temp files land here instead of Program Files
os.chdir(app_data_dir)

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")



import tkinter as tk
import threading
from tkinter import filedialog, messagebox, colorchooser
import customtkinter as ctk

# Import backend logic
from utils import configure_ffmpeg, get_default_font_path, get_whisper_model_path, get_resource_path
from styles import STYLES, get_style_names, get_style_config, get_style_params
from generator import SubtitleGenerator
from license import load_license, verify_license_online, save_license

# Initialize FFmpeg
configure_ffmpeg()


class WhisperDownloadPopup(ctk.CTkToplevel):
    def __init__(self, parent, model):
        super().__init__(parent)

        self.title("Preparing Whisper")
        self.geometry("420x200")
        icon_path = get_resource_path("logo.ico")

        if os.path.exists(icon_path):
            # Sets the top-left window icon
            self.iconbitmap(icon_path)

            # CRITICAL FOR TASKBAR:
            # This "pokes" Windows to refresh the taskbar icon which often gets stuck
            self.after(200, lambda: self.iconbitmap(icon_path))

            # FOR TASK MANAGER: Windows 10/11 requires an internal App ID
            # to link the process to the icon correctly.
            if sys.platform == "win32":
                import ctypes
                myappid = 'mycompany.myproduct.subtitles.v1'  # arbitrary unique string
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        ctk.CTkLabel(
            self,
            text=f"Preparing speech model ({str(model).capitalize()})",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self,
            text="This is a one-time download setup.\nThe app may appear unresponsive — this is normal.\nPlease wait…",
            justify="center",
            text_color="gray"
        ).pack(pady=(0, 20))

        self.bar = ctk.CTkProgressBar(self, mode="indeterminate", progress_color="#008080")
        self.bar.pack(fill="x", padx=40)
        self.bar.start()

    def close(self):
        self.bar.stop()
        self.destroy()


class LicenseDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("License Required")
        self.geometry("420x220")
        icon_path = get_resource_path("logo.ico")

        if os.path.exists(icon_path):
            # Sets the top-left window icon
            self.iconbitmap(icon_path)

            # CRITICAL FOR TASKBAR:
            # This "pokes" Windows to refresh the taskbar icon which often gets stuck
            self.after(200, lambda: self.iconbitmap(icon_path))

            # FOR TASK MANAGER: Windows 10/11 requires an internal App ID
            # to link the process to the icon correctly.
            if sys.platform == "win32":
                import ctypes
                myappid = 'mycompany.myproduct.subtitles.v1'  # arbitrary unique string
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.resizable(False, False)

        self.license_key = None

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Layout
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Enter your Gumroad license key",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text="XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX",
            width=300
        )
        self.entry.grid(row=1, column=0, padx=20, pady=10)
        self.entry.focus()

        self.error_label = ctk.CTkLabel(
            self,
            text="",
            text_color="red"
        )
        self.error_label.grid(row=2, column=0)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Activate",
            width=120,
            command=self.on_submit, fg_color="#008080", hover_color="#006666"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Exit",
            width=120,
            fg_color="gray",
            command=self.on_cancel
        ).pack(side="left", padx=10)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def on_submit(self):
        key = self.entry.get().strip()
        if not key:
            self.error_label.configure(text="Please enter a license key.")
            return
        self.license_key = key
        self.destroy()

    def on_cancel(self):
        self.license_key = None
        self.destroy()


# app.py

def ensure_license(root):
    # 1. Check for existing license file
    lic = load_license()

    if lic:
        # SILENT CHECK: We pass increment_uses=False
        # This checks if the key is valid WITHOUT using up a "seat"
        ok, _ = verify_license_online(lic["license_key"], increment_uses=False)
        if ok:
            return True
        # If silent check fails (e.g. key refunded), we continue down to show the dialog

    # 2. Show the input dialog if no license or silent check failed
    dialog = LicenseDialog(root)
    root.wait_window(dialog)

    if not dialog.license_key:
        return False  # User closed the window

    # 3. ACTIVATION: User just typed a key, so we pass increment_uses=True
    # This WILL consume one of their 3 allowed installs
    ok, response_data = verify_license_online(dialog.license_key, increment_uses=True)

    if ok:
        save_license(dialog.license_key)
        return True
    else:
        # --- Error Popup ---
        error = ctk.CTkToplevel(root)
        error.title("Activation Failed")
        error.geometry("360x180")

        # Icon setup
        icon_path = get_resource_path("logo.ico")
        if os.path.exists(icon_path):
            error.iconbitmap(icon_path)
            error.after(200, lambda: error.iconbitmap(icon_path))
            if sys.platform == "win32":
                import ctypes
                myappid = 'mycompany.myproduct.subtitles.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        error.resizable(False, False)
        error.transient(root)
        error.grab_set()

        # Get specific error message if available
        msg_text = "Invalid or already-used license key."
        if response_data and "message" in response_data:
            msg_text = response_data["message"]

        ctk.CTkLabel(
            error,
            text=msg_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="red",
            wraplength=300
        ).pack(pady=30)

        ctk.CTkButton(
            error,
            text="Try Again",
            command=error.destroy,
            fg_color="#008080",
            hover_color="#006666"
        ).pack()

        root.wait_window(error)
        return False



# --- Global Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SubtitleApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.title("MS Auto Captions")
        self.geometry("950x800")
        icon_path = get_resource_path("logo.ico")

        if os.path.exists(icon_path):
            # Sets the top-left window icon
            self.iconbitmap(icon_path)

            # CRITICAL FOR TASKBAR:
            # This "pokes" Windows to refresh the taskbar icon which often gets stuck
            self.after(200, lambda: self.iconbitmap(icon_path))

            # FOR TASK MANAGER: Windows 10/11 requires an internal App ID
            # to link the process to the icon correctly.
            if sys.platform == "win32":
                import ctypes
                myappid = 'mycompany.myproduct.subtitles.v1'  # arbitrary unique string
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.minsize(800, 700)

        # Main Layout:
        # Row 0: Header (Fixed)
        # Row 1: Content (Scrollable)
        # Row 2: Footer (Fixed - Progress & Button)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Data Variables ---
        self.video_path = ctk.StringVar()
        self.output_path = ctk.StringVar()
        self.font_path = ctk.StringVar(value=get_default_font_path())

        self.style_var = ctk.StringVar()
        self.position_var = ctk.StringVar(value="center")
        self.model_var = ctk.StringVar(value="base")
        self.transcription_mode = ctk.StringVar(value="local")
        self.api_key = ctk.StringVar()

        self.all_caps = ctk.BooleanVar(value=False)
        self.multiline = ctk.BooleanVar(value=False)
        self.font_size = ctk.StringVar(value='60')
        self.words_per_chunk = ctk.StringVar(value='3')

        self.style_params = {}  # Dynamic storage

        self.setup_ui()

        # Init Styles
        self.after(200, lambda: self.on_style_change(None))

    def setup_ui(self):
        # ============================================================
        # 1. HEADER (Top Bar)
        # ============================================================
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)  # Spacer

        # App Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="MS Auto Captions",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        # Theme Switch (Top Right)
        self.switch_mode = ctk.CTkSwitch(
            self.header_frame,
            text="Dark Mode",
            onvalue="Dark", offvalue="Light",
            command=self.toggle_appearance, fg_color="#008080", progress_color="#008080"
        )
        self.switch_mode.select()  # Default to Dark
        self.switch_mode.grid(row=0, column=2, sticky="e")

        # ============================================================
        # 2. SCROLLABLE CONTENT
        # ============================================================
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # --- Section A: Files ---
        self.frame_files = self.create_card(self.scroll_frame, "Project Files", 0)

        self.add_file_row(self.frame_files, 0, "Video File:", self.video_path, self.browse_video)
        self.add_file_row(self.frame_files, 1, "Output Path:", self.output_path, self.browse_output)
        self.add_file_row(self.frame_files, 2, "Font File:", self.font_path, self.browse_font)

        # --- Section B: Configuration (2 Columns) ---
        self.config_grid = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.config_grid.grid(row=1, column=0, sticky="ew", pady=10)
        self.config_grid.grid_columnconfigure(0, weight=1)
        self.config_grid.grid_columnconfigure(1, weight=1)

        # Left Col: Transcription
        self.frame_trans = self.create_card_inner(self.config_grid, "Transcription", row=0, col=0)
        self.frame_trans.grid_columnconfigure(1, weight=1)

        self.radio_local = ctk.CTkRadioButton(
            self.frame_trans, text="Local Whisper", value="local",
            variable=self.transcription_mode, command=self.toggle_api_ui, fg_color="#008080", hover_color="#006666"
        )
        self.radio_local.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.combo_model = ctk.CTkComboBox(self.frame_trans, variable=self.model_var,
                                           values=["tiny", "base", "small", "medium", "large"])
        self.combo_model.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.radio_api = ctk.CTkRadioButton(
            self.frame_trans, text="Groq API", value="api",
            variable=self.transcription_mode, command=self.toggle_api_ui, fg_color="#008080", hover_color="#006666"
        )
        self.radio_api.grid(row=1, column=0, padx=15, pady=10, sticky="w")

        self.entry_api = ctk.CTkEntry(self.frame_trans, textvariable=self.api_key, placeholder_text="API Key", show="*")
        # (API Entry is hidden/shown dynamically)

        # Right Col: Text Settings
        self.frame_text = self.create_card_inner(self.config_grid, "Text Settings", row=0, col=1)
        for i in range(5):
            self.frame_text.grid_rowconfigure(i, pad=4)

        # Grid inside Text Settings
        self.frame_text.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_text, text="Size:").grid(row=0, column=0, padx=15, pady=5, sticky="w")
        ctk.CTkEntry(self.frame_text, textvariable=self.font_size, width=60).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(self.frame_text, text="Chunking:").grid(row=1, column=0, padx=15, pady=5, sticky="w")
        ctk.CTkEntry(self.frame_text, textvariable=self.words_per_chunk, width=60).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(self.frame_text, text="Position:").grid(row=2, column=0, padx=15, pady=5, sticky="w")
        ctk.CTkComboBox(self.frame_text, variable=self.position_var, values=["top", "center", "bottom"],
                        width=100).grid(row=2, column=1, sticky="w")

        ctk.CTkCheckBox(self.frame_text, text="ALL CAPS", variable=self.all_caps, fg_color="#008080", hover_color="#006666").grid(row=3, column=0, columnspan=2,
                                                                                       padx=15, pady=5, sticky="w")
        ctk.CTkCheckBox(self.frame_text, text="Multi-line", variable=self.multiline, fg_color="#008080", hover_color="#006666").grid(row=4, column=0, columnspan=2,
                                                                                          padx=15, pady=5, sticky="w")

        # --- Section C: Style (Full Width) ---
        self.frame_style = self.create_card(self.scroll_frame, "Visual Style", 2)

        # Header Row
        self.style_header = ctk.CTkFrame(self.frame_style, fg_color="transparent")
        self.style_header.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(self.style_header, text="Select Animation:").pack(side="left", padx=(0, 10))
        self.combo_style = ctk.CTkComboBox(
            self.style_header,
            variable=self.style_var,
            values=get_style_names(),
            width=250,
            command=self.on_style_change
        )
        self.combo_style.pack(side="left")

        # Dynamic Content Area
        self.dynamic_frame = ctk.CTkFrame(self.frame_style, fg_color=("gray90", "gray16"), corner_radius=6)
        self.dynamic_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # ============================================================
        # 3. FOOTER (Fixed Bottom)
        # ============================================================
        self.footer = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=("gray85", "#1a1a1a"))
        self.footer.grid(row=2, column=0, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self.footer, height=12, progress_color="#008080")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=30, pady=(15, 5))

        # Status & Button Container
        self.action_box = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.action_box.pack(fill="x", padx=30, pady=(0, 15))

        self.status_label = ctk.CTkLabel(self.action_box, text="Ready", text_color="gray")
        self.status_label.pack(side="left")

        self.btn_generate = ctk.CTkButton(
            self.action_box,
            text="GENERATE VIDEO",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            width=200,
            command=self.start_generation,
            fg_color="#008080", hover_color="#006666"
        )
        self.btn_generate.pack(side="right")

    # --- UI Helpers ---

    def create_card(self, parent, title, row):
        """Full width card with standard styling"""
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=0, sticky="ew", padx=20, pady=10)
        card.grid_columnconfigure(1, weight=1)

        lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        lbl.pack(anchor="w", padx=15, pady=(15, 5))

        div = ctk.CTkFrame(card, height=2, fg_color=("gray80", "gray30"))
        div.pack(fill="x", padx=10, pady=(0, 10))

        return card

    def create_card_inner(self, parent, title, row, col):
        """Half width card with proper spacing and content container"""
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        card.grid_columnconfigure(0, weight=1)

        # Title
        lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"))
        lbl.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # Divider
        div = ctk.CTkFrame(card, height=2, fg_color=("gray80", "gray30"))
        div.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # CONTENT CONTAINER (THIS FIXES THE CRAMPING)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=10, pady=(5, 15))
        content.grid_columnconfigure(1, weight=1)

        return content

    def add_file_row(self, parent, idx, label, var, cmd):
        """Helper to create cleaner file input rows"""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=15, pady=5)
        f.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(f, text=label, width=80, anchor="w").grid(row=0, column=0)
        ctk.CTkEntry(f, textvariable=var).grid(row=0, column=1, sticky="ew", padx=10)
        ctk.CTkButton(f, text="Browse", width=70, command=cmd, fg_color="#008080", hover_color="#006666").grid(row=0, column=2)

    def toggle_appearance(self):
        if self.switch_mode.get() == "Light":
            ctk.set_appearance_mode("Light")
            self.switch_mode.configure(text="Light Mode")
        else:
            ctk.set_appearance_mode("Dark")
            self.switch_mode.configure(text="Dark Mode")

    def toggle_api_ui(self):
        if self.transcription_mode.get() == "api":
            self.combo_model.grid_forget()
            self.entry_api.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        else:
            self.entry_api.grid_forget()
            self.combo_model.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    def browse_video(self):
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.mkv")])
        if f:
            self.video_path.set(f)
            base, ext = os.path.splitext(f)
            self.output_path.set(f"{base}_subtitled.mp4")

    def browse_output(self):
        f = filedialog.asksaveasfilename(defaultextension=".mp4")
        if f: self.output_path.set(f)

    def browse_font(self):
        f = filedialog.askopenfilename(filetypes=[("Font", "*.ttf *.otf")])
        if f: self.font_path.set(f)

    def show_whisper_download_popup(self, model_name):
        popup = ctk.CTkToplevel(self)
        popup.title("Downloading Whisper Model")
        popup.geometry("420x180")
        popup.resizable(False, False)
        popup.transient(self)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text=f"Downloading Whisper model ({model_name.capitalize()})",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            popup,
            text="This is a one-time setup.\nThe app may appear unresponsive — this is normal.\nPlease wait...",
            text_color="gray"
        ).pack(pady=(0, 20))

        bar = ctk.CTkProgressBar(popup, mode="indeterminate")
        bar.pack(fill="x", padx=40)
        bar.start()

        return popup

    def on_style_change(self, event):
        # Clear dynamic frame
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        self.style_params = {}

        try:
            style_idx = int(self.style_var.get().split(":")[0])
        except:
            style_idx = 1

        defaults = get_style_config(style_idx)
        schema = get_style_params(style_idx)

        # 3-Column Grid for Dynamic params
        self.dynamic_frame.grid_columnconfigure(0, weight=1)
        self.dynamic_frame.grid_columnconfigure(1, weight=1)
        self.dynamic_frame.grid_columnconfigure(2, weight=1)

        for i, (key, dtype, label_text) in enumerate(schema):
            default_val = defaults.get(key)

            # Create a mini-cell
            cell = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=10, pady=10)

            ctk.CTkLabel(cell, text=label_text, font=ctk.CTkFont(size=12)).pack(anchor="w")

            if dtype == "color":
                var = ctk.StringVar(value=default_val)
                self.style_params[key] = var

                row = ctk.CTkFrame(cell, fg_color="transparent")
                row.pack(fill="x", pady=(2, 0))

                ent = ctk.CTkEntry(row, textvariable=var, height=28)
                ent.pack(side="left", fill="x", expand=True)

                btn = ctk.CTkButton(row, text="🎨", width=30, height=28,
                                    command=lambda v=var: self.pick_color(v), fg_color="#008080", hover_color="#006666")
                btn.pack(side="left", padx=(5, 0))

            elif dtype == "bool":
                var = ctk.BooleanVar(value=default_val)
                self.style_params[key] = var
                ctk.CTkCheckBox(cell, text="Enable", variable=var, fg_color="#008080", hover_color="#006666").pack(anchor="w", pady=(5, 0))

    def pick_color(self, var):
        c = colorchooser.askcolor(color=var.get())[1]
        if c: var.set(c)

    # --- Generation Logic (Unchanged but connected to new layout) ---
    def update_progress(self, percent=None, msg=None, **kwargs):
        p = percent if percent is not None else kwargs.get('index', 0)
        m = msg if msg is not None else kwargs.get('message', "Processing...")
        try:
            p = float(p)
        except:
            p = 0.0
        self.after(0, lambda: self._update_ui_progress(p, m))

    def _update_ui_progress(self, percent, msg):
        self.progress_bar.set(percent / 100.0)
        self.status_label.configure(text=f"{msg} ({int(percent)}%)", text_color=("gray10", "gray90"))

    def start_generation(self):
        if not self.video_path.get():
            messagebox.showerror("Error", "Please select a video file.")
            return

            # ... (keep your existing font/chunk parsing logic here) ...
        try:
            font_size = int(self.font_size.get())
        except ValueError:
            font_size = 60

        try:
            words_per_chunk = int(self.words_per_chunk.get())
        except ValueError:
            words_per_chunk = 3

        font_path = self.font_path.get()
        if not font_path or not os.path.exists(font_path):
            raise RuntimeError("Font file not found...")

        # --- FIX START ---
        # 1. Get the base defaults
        try:
            style_idx = int(self.style_var.get().split(":")[0])
        except:
            style_idx = 1

        final_style_config = get_style_config(style_idx)

        # 2. OVERRIDE defaults with the values from your UI
        # This loop pulls the actual data from the text boxes and checkboxes
        for key, var in self.style_params.items():
            final_style_config[key] = var.get()

        # 3. Create the main config using the UPDATED style config
        config = {
            "video_path": self.video_path.get(),
            "output_path": self.output_path.get(),
            "font_path": font_path,
            "font_size": font_size,
            "position": self.position_var.get(),
            "all_caps": self.all_caps.get(),
            "multi_line": self.multiline.get(),
            "words_per_chunk": words_per_chunk,
            "use_api": (self.transcription_mode.get() == "api"),
            "api_key": self.api_key.get(),
            "model_size": self.model_var.get(),
            "style_config": final_style_config  # <--- Use the merged config
        }

        self.btn_generate.configure(state="disabled", text="RENDERING...", fg_color="gray")
        self.progress_bar.set(0)

        # SHOW popup ONLY if local whisper
        self.whisper_popup = None
        if self.transcription_mode.get() == "local":
            model = self.model_var.get()
            model_path = get_whisper_model_path(model)
            if not os.path.exists(model_path):
                self.whisper_popup = WhisperDownloadPopup(self, model)

        t = threading.Thread(target=self.run_process, args=(config,))
        t.daemon = True
        t.start()

    def run_process(self, config):
        try:
            gen = SubtitleGenerator(config, None, self.update_progress)
            gen.start_process()

            self.after(0, lambda: messagebox.showinfo(
                "Success", "Video successfully saved!"
            ))

        except Exception as e:
            msg = str(e) if str(e) else "An internal transcription error occurred.\n\nCheck error.log for details."
            self.after(0, lambda: messagebox.showerror("Error", msg))


        finally:
            # CLOSE popup safely
            if self.whisper_popup and self.whisper_popup.winfo_exists():
                self.after(0, self.whisper_popup.close)

            self.after(0, lambda: self.btn_generate.configure(
                state="normal",
                text="GENERATE VIDEO",
                fg_color="#008080"
            ))
            self.after(0, lambda: self.status_label.configure(text="Ready"))


if __name__ == "__main__":
    app = SubtitleApp()

    if not ensure_license(app):
        app.destroy()
        raise SystemExit

    app.deiconify()
    app.mainloop()