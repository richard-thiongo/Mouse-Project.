import os
import sys
import winreg

STARTUP_FOLDER = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup"
)
STARTUP_VBS = os.path.join(STARTUP_FOLDER, "MouseCustomizer.vbs")

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "MouseCustomizer"

def get_pythonw_path():
    """Locate pythonw.exe corresponding to current Python interpreter."""
    dir_name = os.path.dirname(sys.executable)
    pythonw = os.path.join(dir_name, "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return sys.executable

def is_startup_enabled():
    """Check if startup trigger is configured in Startup folder or Registry."""
    if os.path.exists(STARTUP_VBS):
        return True
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, REG_NAME)
            return True
    except (FileNotFoundError, OSError):
        pass
    return False

def set_startup(enable: bool, main_script_path: str = None):
    """Enable or disable starting on Windows boot."""
    if main_script_path is None:
        main_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")

    pythonw = get_pythonw_path()

    if enable:
        # Create silent VBS file in Startup folder
        try:
            os.makedirs(STARTUP_FOLDER, exist_ok=True)
            vbs_content = (
                'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{pythonw}"" ""{main_script_path}"" --minimized", 0, False\n'
            )
            with open(STARTUP_VBS, "w", encoding="utf-8") as f:
                f.write(vbs_content)
        except Exception as e:
            print(f"Error creating startup VBS: {e}")

        # Also add to HKCU Run key for redundancy
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                cmd = f'"{pythonw}" "{main_script_path}" --minimized'
                winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, cmd)
        except Exception as e:
            print(f"Error setting registry startup: {e}")
        return True
    else:
        # Remove VBS file
        if os.path.exists(STARTUP_VBS):
            try:
                os.remove(STARTUP_VBS)
            except Exception as e:
                print(f"Error removing startup VBS: {e}")

        # Remove from registry
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, REG_NAME)
        except (FileNotFoundError, OSError):
            pass
        return False

if __name__ == "__main__":
    print(f"Startup currently enabled: {is_startup_enabled()}")
