import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Discovered application shortcuts
DEFAULT_APPS = [
    {
        "name": "Google Chrome",
        "path": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Google Chrome.lnk",
        "enabled": True
    },
    {
        "name": "Visual Studio Code",
        "path": os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Visual Studio Code\Visual Studio Code.lnk"),
        "enabled": True
    },
    {
        "name": "Antigravity IDE",
        "path": os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Antigravity IDE\Antigravity IDE.lnk"),
        "enabled": True
    }
]

DEFAULT_CONFIG = {
    "engine_enabled": True,
    # Gesture 1: Left-Click + Scroll Window Navigation
    "left_click_scroll_nav": True,
    "nav_mode": "alt_tab",  # "alt_tab" or "alt_esc"
    "drag_threshold": 12,    # pixels of movement to consider as highlighting text
    "reverse_scroll_direction": False,

    # Gesture 2: Smart Double-Click to Paste
    "double_click_paste": True,
    "double_click_interval_ms": 400,

    # Gesture 3: Desktop Triple-Click App Launcher
    "desktop_triple_click_launch": True,
    "desktop_triple_click_apps": DEFAULT_APPS,

    # System & Startup
    "start_on_boot": True,
    "run_silent_on_startup": True,  # Hidden from taskbar, only in system tray
    "minimize_to_tray_on_close": True
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"Error loading config: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False
