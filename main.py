import sys
import os
import tkinter as tk

import config as config_manager
from mouse_engine import MouseEngine
from tray_manager import TrayIconManager
from gui import MouseCustomizerGUI

def main():
    # Load configuration
    cfg = config_manager.load_config()

    # Initialize and start low-level mouse hook engine
    engine = MouseEngine(cfg)
    engine.start()

    # Initialize Tkinter root window
    root = tk.Tk()

    # References for tray callbacks
    gui_instance = None

    def tray_show():
        if gui_instance:
            root.after(0, gui_instance.restore_from_tray)

    def tray_toggle_engine():
        if gui_instance:
            root.after(0, gui_instance.toggle_engine_master)

    def tray_exit():
        if gui_instance:
            root.after(0, gui_instance.exit_app)

    def get_engine_state():
        return engine.config.get("engine_enabled", True)

    tray = TrayIconManager(
        on_show=tray_show,
        on_toggle_engine=tray_toggle_engine,
        on_exit=tray_exit,
        get_engine_state=get_engine_state
    )
    tray.start()

    # Create GUI
    gui_instance = MouseCustomizerGUI(root, config_manager, engine, tray)

    # Check if started with --minimized (e.g. from Windows Startup)
    if "--minimized" in sys.argv:
        root.withdraw()

    try:
        root.mainloop()
    finally:
        engine.stop()
        tray.stop()

if __name__ == "__main__":
    main()
