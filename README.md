# Mouse Customizer

A lightweight Windows application to access connected mice and customize controls, gestures, and automations.

---

## Features

### 1. Left-Click + Scroll: Window Navigation
- **How it works**: Hold down the **Left Mouse Button** and **scroll the wheel** to cycle through open applications (`Alt + Tab`).
- **Release Left Mouse Button** to instantly land on and activate your selected window.
- **Smart Text-Selection Guard**: Dragging across text to highlight/select words automatically keeps normal scrolling enabled so it never triggers accidental window switching.

### 2. Smart Double-Click: Paste Clipboard (Text, Files, Images)
- **How it works**: Double-click on any empty area, text box, editor, or folder to paste recently copied or cut content (`Ctrl + V`).
- **Opening Files Guard**: Uses Microsoft Active Accessibility (`IAccessible`) to recognize when you double-click an actual file, folder, or desktop shortcut—safely opening the file instead of pasting!
- **Drag Guard**: If you drag the mouse while clicking, paste is suppressed so normal selection and drag-and-drop are never interrupted.

### 3. Desktop Triple-Click App Launcher
- **How it works**: When on your desktop background, click the **Left Mouse Button three times** in quick succession.
- **Automatically launches your preferred productivity apps**:
  - Google Chrome
  - Visual Studio Code
  - Antigravity IDE
- **Customizable in GUI**:
  - Add any app, script, or shortcut (`.exe`, `.lnk`, `.bat`, `.cmd`) with the file browser.
  - Remove or toggle individual apps.
  - Test launch apps on demand.

### 4. Windows Startup & Silent Mode (No Taskbar Presence)
- **Zero Taskbar Footprint**: Configured to run silently in the **Windows System Tray** on startup (`pythonw.exe main.py --minimized`).
- **Startup Integration**: Registered in your Windows Startup directory (`shell:startup`) and User Registry (`HKCU\...\Run`).
- **Tray Controls**:
  - Right-click the mouse icon in your notification tray (near the clock) to pause/resume or exit.
  - Double-click the tray icon to open the GUI settings window anytime.

---

## How to Run

### Double-Click Launchers
- **`run_silent.vbs`**: Starts silently straight into the System Tray with no console and no taskbar icon.
- **`run.bat`**: Starts with a visible console window (useful for logs/diagnostics).

### Command Line
```powershell
# Open settings window
python main.py

# Run silently in background (tray only, hidden from taskbar)
pythonw main.py --minimized
```
