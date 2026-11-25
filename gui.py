import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import ctypes
import os

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from raw_input_devices import get_connected_mice
from startup_manager import is_startup_enabled, set_startup

# Color Palette (Slate Dark Modern Theme)
BG_MAIN = "#0F172A"       # Deep slate navy
BG_CARD = "#1E293B"       # Card surface
BG_INPUT = "#334155"      # Input / inner card
TEXT_MAIN = "#F8FAFC"     # White text
TEXT_MUTED = "#94A3B8"    # Soft gray text
ACCENT_BLUE = "#3B82F6"   # Primary blue
ACCENT_BLUE_HOVER = "#2563EB"
ACCENT_GREEN = "#10B981"  # Success / active
ACCENT_RED = "#EF4444"    # Alert / paused
BORDER_COLOR = "#475569"

FONT_HEADING = ("Segoe UI", 15, "bold")
FONT_SUBHEADING = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 9)

class MouseCustomizerGUI:
    def __init__(self, root, config_manager, engine, tray_manager):
        self.root = root
        self.config_manager = config_manager
        self.engine = engine
        self.tray_manager = tray_manager

        self.config = self.config_manager.load_config()

        self.root.title("Mouse Customizer")
        self.root.geometry("720x760")
        self.root.minsize(680, 680)
        self.root.configure(bg=BG_MAIN)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close_clicked)
        self.engine.on_gesture_event = self.on_engine_gesture_event

        self._init_vars()
        self._build_ui()
        self.refresh_devices()

    def _init_vars(self):
        self.var_engine_enabled = tk.BooleanVar(value=self.config.get("engine_enabled", True))
        
        # Gesture 1: Left Click + Scroll Nav
        self.var_gesture_nav = tk.BooleanVar(value=self.config.get("left_click_scroll_nav", True))
        self.var_nav_mode = tk.StringVar(value=self.config.get("nav_mode", "alt_tab"))
        self.var_drag_thresh = tk.IntVar(value=self.config.get("drag_threshold", 12))
        self.var_reverse_scroll = tk.BooleanVar(value=self.config.get("reverse_scroll_direction", False))

        # Gesture 2: Double-Click Paste
        self.var_double_click_paste = tk.BooleanVar(value=self.config.get("double_click_paste", True))
        self.var_dc_interval = tk.IntVar(value=self.config.get("double_click_interval_ms", 400))

        # Gesture 3: Desktop Triple-Click App Launcher
        self.var_triple_click_launch = tk.BooleanVar(value=self.config.get("desktop_triple_click_launch", True))
        self.apps_list = list(self.config.get("desktop_triple_click_apps", []))

        # System
        self.var_startup = tk.BooleanVar(value=is_startup_enabled())
        self.var_minimize_on_close = tk.BooleanVar(value=self.config.get("minimize_to_tray_on_close", True))

        self.gesture_counter = 0

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_MAIN, padding=[16, 8], font=FONT_SUBHEADING)
        style.map("TNotebook.Tab", background=[("selected", ACCENT_BLUE)], foreground=[("selected", "#FFFFFF")])

        main_frame = tk.Frame(self.root, bg=BG_MAIN)
        main_frame.pack(fill="both", expand=True, padx=16, pady=12)

        # 1. HEADER BAR
        header = tk.Frame(main_frame, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=16, pady=12)
        header.pack(fill="x", pady=(0, 10))

        title_box = tk.Frame(header, bg=BG_CARD)
        title_box.pack(side="left")
        tk.Label(title_box, text="Mouse Customizer", font=FONT_HEADING, fg=TEXT_MAIN, bg=BG_CARD).pack(anchor="w")
        tk.Label(title_box, text="Hardware Automation & Gestures", font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")

        right_box = tk.Frame(header, bg=BG_CARD)
        right_box.pack(side="right")

        self.lbl_status_pill = tk.Label(
            right_box, text="● ENGINE ACTIVE", font=("Segoe UI", 9, "bold"),
            fg=ACCENT_GREEN, bg=BG_INPUT, padx=10, pady=4
        )
        self.lbl_status_pill.pack(side="left", padx=(0, 10))

        self.btn_master_toggle = tk.Button(
            right_box, text="Disable", font=FONT_SMALL, bg=ACCENT_BLUE, fg="#FFFFFF",
            relief="flat", padx=12, pady=4, cursor="hand2", command=self.toggle_engine_master
        )
        self.btn_master_toggle.pack(side="left")

        # 2. NOTEBOOK TABS
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True, pady=(0, 10))

        # Tab 1: Gestures & Mouse Actions
        tab_gestures = tk.Frame(notebook, bg=BG_MAIN, padx=4, pady=8)
        notebook.add(tab_gestures, text=" Gestures & Actions ")

        # Tab 2: Desktop Triple-Click App Launcher
        tab_apps = tk.Frame(notebook, bg=BG_MAIN, padx=4, pady=8)
        notebook.add(tab_apps, text=" Desktop App Launcher ")

        # Tab 3: Hardware & Startup
        tab_system = tk.Frame(notebook, bg=BG_MAIN, padx=4, pady=8)
        notebook.add(tab_system, text=" Devices & Startup ")

        # BUILD TAB 1: GESTURES
        self._build_tab_gestures(tab_gestures)

        # BUILD TAB 2: APP LAUNCHER
        self._build_tab_apps(tab_apps)

        # BUILD TAB 3: HARDWARE & SYSTEM
        self._build_tab_system(tab_system)

        # 3. LIVE GESTURE ACTIVITY BAR
        status_card = tk.Frame(main_frame, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=14, pady=8)
        status_card.pack(fill="x", pady=(0, 8))

        self.lbl_live_activity = tk.Label(
            status_card, text="Ready. Gestures and automations are listening in the background.",
            font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD
        )
        self.lbl_live_activity.pack(side="left")

        # 4. BOTTOM ACTION BUTTONS
        btn_bar = tk.Frame(main_frame, bg=BG_MAIN)
        btn_bar.pack(fill="x")

        tk.Button(
            btn_bar, text="Minimize to Tray (Run Silent)", font=FONT_BODY, bg=BG_CARD,
            fg=TEXT_MAIN, relief="flat", padx=14, pady=6, cursor="hand2", command=self.minimize_to_tray
        ).pack(side="left")

        tk.Button(
            btn_bar, text="Exit Application", font=FONT_BODY, bg="#991B1B", fg="#FFFFFF",
            relief="flat", padx=14, pady=6, cursor="hand2", command=self.exit_app
        ).pack(side="right")

        self.update_master_ui()

    def _build_tab_gestures(self, parent):
        # Card 1: Left Click + Scroll Nav
        c1 = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=16, pady=12)
        c1.pack(fill="x", pady=(0, 10))

        head1 = tk.Frame(c1, bg=BG_CARD)
        head1.pack(fill="x", pady=(0, 4))
        tk.Label(head1, text="1. Left-Click + Scroll: Window Navigation", font=FONT_SUBHEADING, fg=TEXT_MAIN, bg=BG_CARD).pack(side="left")
        tk.Checkbutton(
            head1, text="Enabled", variable=self.var_gesture_nav, font=FONT_SMALL, fg=ACCENT_GREEN,
            selectcolor=BG_INPUT, activebackground=BG_CARD, bg=BG_CARD, command=self.on_setting_changed
        ).pack(side="right")

        tk.Label(
            c1, text="Hold Left Mouse Button and scroll wheel to cycle windows. Highlight text as normal without triggering.",
            font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD, justify="left"
        ).pack(anchor="w", pady=(0, 8))

        sub1 = tk.Frame(c1, bg=BG_INPUT, padx=12, pady=8)
        sub1.pack(fill="x")

        # Nav Style
        r_mode = tk.Frame(sub1, bg=BG_INPUT)
        r_mode.pack(fill="x", pady=2)
        tk.Label(r_mode, text="Style:", font=FONT_BODY, fg=TEXT_MAIN, bg=BG_INPUT, width=14, anchor="w").pack(side="left")
        tk.Radiobutton(
            r_mode, text="Task Switcher (Alt + Tab)", variable=self.var_nav_mode, value="alt_tab",
            font=FONT_SMALL, fg=TEXT_MAIN, bg=BG_INPUT, selectcolor=BG_CARD, command=self.on_setting_changed
        ).pack(side="left", padx=(0, 10))
        tk.Radiobutton(
            r_mode, text="Instant Cycle (Alt + Esc)", variable=self.var_nav_mode, value="alt_esc",
            font=FONT_SMALL, fg=TEXT_MAIN, bg=BG_INPUT, selectcolor=BG_CARD, command=self.on_setting_changed
        ).pack(side="left")

        # Drag Sensitivity
        r_sens = tk.Frame(sub1, bg=BG_INPUT)
        r_sens.pack(fill="x", pady=4)
        tk.Label(r_sens, text="Text Drag Guard:", font=FONT_BODY, fg=TEXT_MAIN, bg=BG_INPUT, width=14, anchor="w").pack(side="left")
        tk.Scale(
            r_sens, from_=4, to=30, orient="horizontal", variable=self.var_drag_thresh,
            bg=BG_INPUT, fg=TEXT_MAIN, highlightthickness=0, troughcolor=BG_CARD,
            activebackground=ACCENT_BLUE, command=lambda v: self.on_setting_changed()
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.lbl_thresh_val = tk.Label(r_sens, text=f"{self.var_drag_thresh.get()} px", font=FONT_MONO, fg=ACCENT_BLUE, bg=BG_INPUT, width=5)
        self.lbl_thresh_val.pack(side="left")

        # Invert Scroll
        tk.Checkbutton(
            sub1, text="Invert scroll direction", variable=self.var_reverse_scroll,
            font=FONT_SMALL, fg=TEXT_MAIN, selectcolor=BG_CARD, bg=BG_INPUT, command=self.on_setting_changed
        ).pack(anchor="w", pady=(2, 0))

        # Card 2: Smart Double-Click to Paste
        c2 = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=16, pady=12)
        c2.pack(fill="x", pady=(0, 10))

        head2 = tk.Frame(c2, bg=BG_CARD)
        head2.pack(fill="x", pady=(0, 4))
        tk.Label(head2, text="2. Smart Double-Click: Paste Clipboard", font=FONT_SUBHEADING, fg=TEXT_MAIN, bg=BG_CARD).pack(side="left")
        tk.Checkbutton(
            head2, text="Enabled", variable=self.var_double_click_paste, font=FONT_SMALL, fg=ACCENT_GREEN,
            selectcolor=BG_INPUT, activebackground=BG_CARD, bg=BG_CARD, command=self.on_setting_changed
        ).pack(side="right")

        tk.Label(
            c2, text="Double-click in empty spaces, text boxes, or folders to paste clipboard contents (text, cut/copied files).\n"
                     "Smart Guard: Opening actual files/shortcuts or dragging objects is safely preserved and will NOT paste.",
            font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD, justify="left"
        ).pack(anchor="w", pady=(0, 8))

        sub2 = tk.Frame(c2, bg=BG_INPUT, padx=12, pady=8)
        sub2.pack(fill="x")

        r_dc = tk.Frame(sub2, bg=BG_INPUT)
        r_dc.pack(fill="x", pady=2)
        tk.Label(r_dc, text="Double-Click Speed:", font=FONT_BODY, fg=TEXT_MAIN, bg=BG_INPUT, width=18, anchor="w").pack(side="left")
        tk.Scale(
            r_dc, from_=250, to=600, orient="horizontal", variable=self.var_dc_interval,
            bg=BG_INPUT, fg=TEXT_MAIN, highlightthickness=0, troughcolor=BG_CARD,
            activebackground=ACCENT_BLUE, command=lambda v: self.on_setting_changed()
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.lbl_dc_val = tk.Label(r_dc, text=f"{self.var_dc_interval.get()} ms", font=FONT_MONO, fg=ACCENT_BLUE, bg=BG_INPUT, width=6)
        self.lbl_dc_val.pack(side="left")

    def _build_tab_apps(self, parent):
        card = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=16, pady=12)
        card.pack(fill="both", expand=True)

        head = tk.Frame(card, bg=BG_CARD)
        head.pack(fill="x", pady=(0, 4))
        tk.Label(head, text="Desktop Triple-Click App Launcher", font=FONT_SUBHEADING, fg=TEXT_MAIN, bg=BG_CARD).pack(side="left")
        tk.Checkbutton(
            head, text="Enabled", variable=self.var_triple_click_launch, font=FONT_SMALL, fg=ACCENT_GREEN,
            selectcolor=BG_INPUT, activebackground=BG_CARD, bg=BG_CARD, command=self.on_setting_changed
        ).pack(side="right")

        tk.Label(
            card, text="Clicking three times on your desktop background will instantly open your preferred productivity apps.\n"
                       "Add, remove, or toggle applications below:",
            font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD, justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # App List Box
        list_container = tk.Frame(card, bg=BG_INPUT, padx=8, pady=8)
        list_container.pack(fill="both", expand=True, pady=(0, 10))

        self.app_listbox = tk.Listbox(
            list_container, bg=BG_MAIN, fg=TEXT_MAIN, font=FONT_BODY,
            selectbackground=ACCENT_BLUE, selectforeground="#FFFFFF",
            relief="flat", highlightthickness=1, highlightbackground=BORDER_COLOR
        )
        self.app_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.app_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.app_listbox.config(yscrollcommand=scrollbar.set)

        self._refresh_apps_listbox()

        # Action Buttons
        btn_box = tk.Frame(card, bg=BG_CARD)
        btn_box.pack(fill="x")

        tk.Button(
            btn_box, text="+ Add Application...", font=FONT_SMALL, bg=ACCENT_BLUE, fg="#FFFFFF",
            relief="flat", padx=10, pady=4, cursor="hand2", command=self.add_app_dialog
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_box, text="− Remove Selected", font=FONT_SMALL, bg=BG_INPUT, fg=TEXT_MAIN,
            relief="flat", padx=10, pady=4, cursor="hand2", command=self.remove_selected_app
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            btn_box, text="⚡ Launch Apps Now (Test)", font=FONT_SMALL, bg=ACCENT_GREEN, fg="#FFFFFF",
            relief="flat", padx=10, pady=4, cursor="hand2", command=self.test_launch_apps
        ).pack(side="right")

    def _build_tab_system(self, parent):
        # Startup Card
        c_start = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=16, pady=12)
        c_start.pack(fill="x", pady=(0, 10))

        tk.Label(c_start, text="Windows Startup (Silent Mode)", font=FONT_SUBHEADING, fg=TEXT_MAIN, bg=BG_CARD).pack(anchor="w", pady=(0, 4))
        
        tk.Checkbutton(
            c_start, text="Run on Windows Startup (Silently in System Tray - hidden from Taskbar)",
            variable=self.var_startup, font=FONT_BODY, fg=TEXT_MAIN, selectcolor=BG_INPUT,
            activebackground=BG_CARD, bg=BG_CARD, command=self.toggle_startup
        ).pack(anchor="w", pady=2)

        tk.Label(
            c_start, text="When enabled, launches automatically on logon without any taskbar button or terminal window.\n"
                         "Access settings anytime via the mouse icon in your notification tray near the clock.",
            font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD, justify="left"
        ).pack(anchor="w", padx=22, pady=(0, 6))

        tk.Checkbutton(
            c_start, text="Close button (X) minimizes to tray instead of quitting",
            variable=self.var_minimize_on_close, font=FONT_BODY, fg=TEXT_MAIN, selectcolor=BG_INPUT,
            activebackground=BG_CARD, bg=BG_CARD, command=self.on_setting_changed
        ).pack(anchor="w", pady=2)

        # Hardware Devices Card
        c_dev = tk.Frame(parent, bg=BG_CARD, highlightthickness=1, highlightbackground=BORDER_COLOR, padx=16, pady=12)
        c_dev.pack(fill="both", expand=True)

        d_head = tk.Frame(c_dev, bg=BG_CARD)
        d_head.pack(fill="x", pady=(0, 6))
        tk.Label(d_head, text="Connected Mouse Hardware (Raw Input)", font=FONT_SUBHEADING, fg=TEXT_MAIN, bg=BG_CARD).pack(side="left")
        tk.Button(
            d_head, text="⟳ Refresh", font=FONT_SMALL, bg=BG_INPUT, fg=TEXT_MAIN,
            relief="flat", padx=8, pady=2, cursor="hand2", command=self.refresh_devices
        ).pack(side="right")

        self.dev_list_frame = tk.Frame(c_dev, bg=BG_CARD)
        self.dev_list_frame.pack(fill="both", expand=True)

    def _refresh_apps_listbox(self):
        self.app_listbox.delete(0, tk.END)
        for app in self.apps_list:
            status = "✔" if app.get("enabled", True) else "✕"
            self.app_listbox.insert(tk.END, f" [{status}]  {app.get('name', 'App')}  —  {app.get('path', '')}")

    def add_app_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Select Application or Shortcut",
            filetypes=[("Executables & Shortcuts", "*.exe;*.lnk;*.bat;*.cmd"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        app_name = simpledialog.askstring("Application Name", "Enter a name for this app:", initialvalue=base_name)
        if not app_name:
            app_name = base_name

        self.apps_list.append({
            "name": app_name,
            "path": os.path.normpath(file_path),
            "enabled": True
        })
        self._refresh_apps_listbox()
        self.on_setting_changed()

    def remove_selected_app(self):
        sel = self.app_listbox.curselection()
        if not sel:
            messagebox.showinfo("Select App", "Please click on an application from the list to remove it.")
            return
        idx = sel[0]
        del self.apps_list[idx]
        self._refresh_apps_listbox()
        self.on_setting_changed()

    def test_launch_apps(self):
        self.engine.launch_desktop_apps()
        self.lbl_live_activity.config(text="⚡ Desktop apps launch triggered successfully!", fg=ACCENT_GREEN)

    def refresh_devices(self):
        for widget in self.dev_list_frame.winfo_children():
            widget.destroy()

        devices = get_connected_mice()
        if not devices:
            tk.Label(self.dev_list_frame, text="No mouse devices detected.", font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
            return

        for dev in devices:
            row = tk.Frame(self.dev_list_frame, bg=BG_INPUT, padx=10, pady=5)
            row.pack(fill="x", pady=2)
            tk.Label(row, text="●", fg=ACCENT_GREEN, bg=BG_INPUT, font=FONT_SMALL).pack(side="left", padx=(0, 6))
            tk.Label(row, text=dev["name"], font=("Segoe UI", 9, "bold"), fg=TEXT_MAIN, bg=BG_INPUT).pack(side="left")
            tk.Label(row, text=f"({dev['type']})", font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_INPUT).pack(side="left", padx=(6, 0))

    def on_setting_changed(self):
        thresh_val = self.var_drag_thresh.get()
        dc_val = self.var_dc_interval.get()
        if hasattr(self, "lbl_thresh_val"):
            self.lbl_thresh_val.config(text=f"{thresh_val} px")
        if hasattr(self, "lbl_dc_val"):
            self.lbl_dc_val.config(text=f"{dc_val} ms")

        new_config = {
            "engine_enabled": self.var_engine_enabled.get(),
            "left_click_scroll_nav": self.var_gesture_nav.get(),
            "nav_mode": self.var_nav_mode.get(),
            "drag_threshold": thresh_val,
            "reverse_scroll_direction": self.var_reverse_scroll.get(),
            "double_click_paste": self.var_double_click_paste.get(),
            "double_click_interval_ms": dc_val,
            "desktop_triple_click_launch": self.var_triple_click_launch.get(),
            "desktop_triple_click_apps": self.apps_list,
            "start_on_boot": self.var_startup.get(),
            "run_silent_on_startup": True,
            "minimize_to_tray_on_close": self.var_minimize_on_close.get()
        }
        self.config_manager.save_config(new_config)
        self.engine.update_config(new_config)
        self.update_master_ui()

    def toggle_engine_master(self):
        current = self.var_engine_enabled.get()
        self.var_engine_enabled.set(not current)
        self.on_setting_changed()
        if self.tray_manager:
            self.tray_manager.update_icon()

    def update_master_ui(self):
        enabled = self.var_engine_enabled.get()
        if enabled:
            self.lbl_status_pill.config(text="● ENGINE ACTIVE", fg=ACCENT_GREEN)
            self.btn_master_toggle.config(text="Disable", bg=BG_INPUT, fg=TEXT_MAIN)
        else:
            self.lbl_status_pill.config(text="■ ENGINE PAUSED", fg=ACCENT_RED)
            self.btn_master_toggle.config(text="Enable", bg=ACCENT_GREEN, fg="#FFFFFF")

    def toggle_startup(self):
        want_startup = self.var_startup.get()
        set_startup(want_startup)
        self.on_setting_changed()

    def on_engine_gesture_event(self, event_type):
        def update_label():
            if event_type == "start":
                self.lbl_live_activity.config(text="⚡ Navigating: Cycling windows with scroll wheel...", fg=ACCENT_BLUE)
            elif event_type == "step":
                self.gesture_counter += 1
                self.lbl_live_activity.config(text=f"⚡ Cycling windows (step #{self.gesture_counter})... Release Left-Click to select.", fg=ACCENT_GREEN)
            elif event_type == "end":
                self.lbl_live_activity.config(text="✔ Switched window! Ready.", fg=TEXT_MAIN)
                self.gesture_counter = 0
            elif event_type == "double_click_paste":
                self.lbl_live_activity.config(text="📋 Smart Double-Click: Clipboard contents pasted (Ctrl+V)!", fg=ACCENT_GREEN)
            elif event_type == "triple_click_launch":
                self.lbl_live_activity.config(text="🚀 Desktop Triple-Click: Launching Chrome, VS Code & Antigravity IDE!", fg=ACCENT_GREEN)
            elif event_type == "cancel":
                self.lbl_live_activity.config(text="✕ Action cancelled.", fg=ACCENT_RED)
                self.gesture_counter = 0

        self.root.after(0, update_label)

    def on_close_clicked(self):
        if self.var_minimize_on_close.get():
            self.minimize_to_tray()
        else:
            self.exit_app()

    def minimize_to_tray(self):
        self.root.withdraw()

    def restore_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def exit_app(self):
        if self.engine:
            self.engine.stop()
        if self.tray_manager:
            self.tray_manager.stop()
        self.root.destroy()
