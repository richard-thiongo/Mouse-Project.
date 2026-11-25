import ctypes
from ctypes import wintypes
import re

user32 = ctypes.windll.user32

class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [
        ('hDevice', wintypes.HANDLE),
        ('dwType', wintypes.DWORD)
    ]

RIM_TYPEMOUSE = 0
RIDI_DEVICENAME = 0x20000007

def get_connected_mice():
    """
    Returns a list of dictionaries with information about each connected mouse device.
    """
    devices = []
    num_devices = wintypes.UINT()
    res = user32.GetRawInputDeviceList(None, ctypes.byref(num_devices), ctypes.sizeof(RAWINPUTDEVICELIST))
    if num_devices.value == 0:
        return devices

    device_list = (RAWINPUTDEVICELIST * num_devices.value)()
    user32.GetRawInputDeviceList(device_list, ctypes.byref(num_devices), ctypes.sizeof(RAWINPUTDEVICELIST))

    mouse_index = 1
    for dev in device_list:
        if dev.dwType == RIM_TYPEMOUSE:
            name_len = wintypes.UINT()
            user32.GetRawInputDeviceInfoW(dev.hDevice, RIDI_DEVICENAME, None, ctypes.byref(name_len))
            if name_len.value > 0:
                name_buf = ctypes.create_unicode_buffer(name_len.value)
                user32.GetRawInputDeviceInfoW(dev.hDevice, RIDI_DEVICENAME, name_buf, ctypes.byref(name_len))
                raw_path = value
            else:
                raw_path = "Unknown Device"

            friendly_name, dev_type = parse_mouse_info(raw_path, mouse_index)
            devices.append({
                "index": mouse_index,
                "handle": str(dev.hDevice),
                "name": friendly_name,
                "type": dev_type,
                "raw_path": raw_path
            })
            mouse_index += 1

    return devices

def parse_mouse_info(raw_path, idx):
    """
    Parses hardware ID and returns friendly name and device category.
    """
    raw_path_upper = raw_path.upper()
    if "SYN" in raw_path_upper or "TOUCHPAD" in raw_path_upper or "ELAN" in raw_path_upper or "ALPS" in raw_path_upper:
        return f"Touchpad / Trackpad ({idx})", "Built-in Touchpad"
    
    vid_pid = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", raw_path_upper)
    if vid_pid:
        vid, pid = vid_pid.group(1), vid_pid.group(2)
        return f"USB / Wireless Mouse [VID:{vid} PID:{pid}]", "External Mouse"
    
    if "RDP_MOU" in raw_path_upper or "VIRTUAL" in raw_path_upper:
        return f"Virtual / Remote Pointer ({idx})", "Virtual Pointer"

    return f"Standard Pointing Device ({idx})", "Mouse"

if __name__ == "__main__":
    mice = get_connected_mice()
    print(f"Found {len(mice)} mouse devices:")
    for m in mice:
        print(f" - {m['name']} ({m['type']})")
