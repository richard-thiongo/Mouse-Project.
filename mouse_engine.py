import ctypes
from ctypes import wintypes
import threading
import time
import os

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
oleacc = ctypes.windll.oleacc

# Hook & Message Constants
WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_MOUSEWHEEL = 0x020A
WM_QUIT = 0x0012

# Virtual Key Constants
VK_TAB = 0x09
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12       # Alt key
VK_ESCAPE = 0x1B
KEYEVENTF_KEYUP = 0x0002

class POINT(ctypes.Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

class VARIANT(ctypes.Structure):
    _fields_ = [
        ('vt', wintypes.WORD),
        ('wReserved1', wintypes.WORD),
        ('wReserved2', wintypes.WORD),
        ('wReserved3', wintypes.WORD),
        ('lVal', wintypes.LONG),
        ('padding', ctypes.c_byte * 8)
    ]

class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('pt_x', wintypes.LONG),
        ('pt_y', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('flags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.c_ulonglong)
    ]

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32.CallNextHookEx.restype = ctypes.c_longlong
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]

def press_key(vk):
    user32.keybd_event(vk, 0, 0, 0)

def release_key(vk):
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def get_class_name(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def is_desktop_at_point(x, y):
    """Check if point is over the Windows desktop canvas."""
    pt = POINT(x, y)
    hwnd = user32.WindowFromPoint(pt)
    if not hwnd:
        return False
    curr = hwnd
    for _ in range(6):
        cls = get_class_name(curr)
        if cls in ("Progman", "WorkerW", "SHELLDLL_DefView", "SysListView32"):
            return True
        parent = user32.GetParent(curr)
        if not parent or parent == curr:
            break
        curr = parent
    return False

def is_cursor_over_file_item(x, y):
    """
    Check if the cursor is specifically over a file/folder/shortcut item.
    Uses Microsoft Active Accessibility (IAccessible) to distinguish
    between clicking an actual file/icon vs empty space.
    """
    try:
        pt = POINT(x, y)
        pacc = ctypes.c_void_p()
        var_child = VARIANT()
        res = oleacc.AccessibleObjectFromPoint(pt, ctypes.byref(pacc), ctypes.byref(var_child))
        if res == 0 and pacc.value:
            vtable = ctypes.cast(pacc, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            # Method 13 in IAccessible vtable is get_accRole
            get_accRole = ctypes.WINFUNCTYPE(wintypes.HRESULT, ctypes.c_void_p, VARIANT, ctypes.POINTER(VARIANT))(vtable[13])
            var_role = VARIANT()
            hres = get_accRole(pacc, var_child, ctypes.byref(var_role))
            # Method 2 is Release
            release = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vtable[2])
            release(pacc)
            if hres == 0:
                # ROLE_LISTITEM = 34, ROLE_OUTLINEITEM = 35, ROLE_LINK = 30
                return var_role.lVal in (34, 35, 30)
    except Exception:
        pass
    return False

class MouseEngine:
    def __init__(self, config):
        self.config = config
        self.hook_id = None
        self.thread_id = None
        self.hook_proc_ref = None
        self.thread = None
        self.is_running = False

        # State tracking for Gesture 1: Left Click + Scroll
        self.left_down = False
        self.start_x = 0
        self.start_y = 0
        self.is_dragging = False
        self.in_switch_mode = False

        # State tracking for Click Streaks (Double-Click & Triple-Click)
        self.click_streak = 0
        self.last_click_time = 0.0
        self.last_click_pos = (0, 0)
        self.click_was_on_desktop = False
        self.click_was_over_file = False
        self.pending_paste = False

        # Callback for UI notification
        self.on_gesture_event = None

    def update_config(self, new_config):
        self.config = new_config

    def launch_desktop_apps(self):
        """Launch the apps configured for Desktop Triple-Click."""
        apps = self.config.get("desktop_triple_click_apps", [])
        for app in apps:
            if app.get("enabled", True):
                path = app.get("path", "")
                if path and os.path.exists(path):
                    try:
                        os.startfile(path)
                    except Exception as e:
                        print(f"Error launching {path}: {e}")

    def _send_paste(self):
        """Simulate Ctrl + V with appropriate timing."""
        time.sleep(0.04)  # Small delay so active control places cursor
        press_key(VK_CONTROL)
        press_key(ord('V'))
        release_key(ord('V'))
        release_key(VK_CONTROL)

    def _hook_procedure(self, nCode, wParam, lParam):
        if nCode < 0:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Check master switch
        if not self.config.get("engine_enabled", True):
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        hook_data = MSLLHOOKSTRUCT.from_address(lParam)
        x = hook_data.pt_x
        y = hook_data.pt_y
        now = time.time()

        # Handle Left Button Down
        if wParam == WM_LBUTTONDOWN:
            self.left_down = True
            self.start_x = x
            self.start_y = y
            self.is_dragging = False
            self.in_switch_mode = False

            # Check click interval and distance
            interval = self.config.get("double_click_interval_ms", 400) / 1000.0
            dt = now - self.last_click_time
            dx = abs(x - self.last_click_pos[0])
            dy = abs(y - self.last_click_pos[1])

            if dt <= interval and dx <= 10 and dy <= 10:
                self.click_streak += 1
            else:
                self.click_streak = 1

            self.last_click_time = now
            self.last_click_pos = (x, y)
            self.click_was_on_desktop = is_desktop_at_point(x, y)
            self.click_was_over_file = is_cursor_over_file_item(x, y)

            # Triple-Click on Desktop check
            if self.click_streak == 3 and self.config.get("desktop_triple_click_launch", True):
                if self.click_was_on_desktop:
                    threading.Thread(target=self.launch_desktop_apps, daemon=True).start()
                    self.click_streak = 0
                    if self.on_gesture_event:
                        self.on_gesture_event("triple_click_launch")

            # Double-Click to Paste check
            elif self.click_streak == 2 and self.config.get("double_click_paste", True):
                # Only paste if NOT over an actual file/shortcut
                if not self.click_was_over_file:
                    self.pending_paste = True

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Handle Mouse Movement (detect dragging / text selection)
        elif wParam == WM_MOUSEMOVE:
            if self.left_down:
                dx = abs(x - self.start_x)
                dy = abs(y - self.start_y)
                drag_limit = self.config.get("drag_threshold", 12)
                if dx > drag_limit or dy > drag_limit:
                    self.is_dragging = True
                    self.pending_paste = False  # Cancel paste if user is dragging
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Handle Mouse Wheel (Gesture 1: Left Click + Scroll)
        elif wParam == WM_MOUSEWHEEL:
            gesture_enabled = self.config.get("left_click_scroll_nav", True)
            if gesture_enabled and self.left_down and not self.is_dragging:
                # Cancel pending paste if user scrolls
                self.pending_paste = False
                self.click_streak = 0

                raw_delta = (hook_data.mouseData >> 16) & 0xFFFF
                delta = ctypes.c_short(raw_delta).value

                if self.config.get("reverse_scroll_direction", False):
                    delta = -delta

                nav_mode = self.config.get("nav_mode", "alt_tab")

                if not self.in_switch_mode:
                    self.in_switch_mode = True
                    if self.on_gesture_event:
                        self.on_gesture_event("start")
                    if nav_mode == "alt_tab":
                        press_key(VK_MENU)

                if nav_mode == "alt_tab":
                    if delta < 0:
                        press_key(VK_TAB)
                        release_key(VK_TAB)
                    else:
                        press_key(VK_SHIFT)
                        press_key(VK_TAB)
                        release_key(VK_TAB)
                        release_key(VK_SHIFT)
                elif nav_mode == "alt_esc":
                    if delta < 0:
                        press_key(VK_MENU)
                        press_key(VK_ESCAPE)
                        release_key(VK_ESCAPE)
                        release_key(VK_MENU)
                    else:
                        press_key(VK_MENU)
                        press_key(VK_SHIFT)
                        press_key(VK_ESCAPE)
                        release_key(VK_ESCAPE)
                        release_key(VK_SHIFT)
                        release_key(VK_MENU)

                if self.on_gesture_event:
                    self.on_gesture_event("step")

                return 1

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Handle Left Button Up
        elif wParam == WM_LBUTTONUP:
            was_in_switch = self.in_switch_mode
            self.left_down = False
            self.in_switch_mode = False

            # Check if pending paste should execute
            if self.pending_paste:
                self.pending_paste = False
                if not self.is_dragging and not was_in_switch:
                    threading.Thread(target=self._send_paste, daemon=True).start()
                    if self.on_gesture_event:
                        self.on_gesture_event("double_click_paste")

            self.is_dragging = False

            if was_in_switch:
                nav_mode = self.config.get("nav_mode", "alt_tab")
                if nav_mode == "alt_tab":
                    release_key(VK_MENU)
                if self.on_gesture_event:
                    self.on_gesture_event("end")
                return 1

            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        # Cancel gesture if Right button is clicked during navigation
        elif wParam == WM_RBUTTONDOWN:
            self.pending_paste = False
            if self.in_switch_mode:
                press_key(VK_ESCAPE)
                release_key(VK_ESCAPE)
                release_key(VK_MENU)
                self.in_switch_mode = False
                self.left_down = False
                if self.on_gesture_event:
                    self.on_gesture_event("cancel")
                return 1

        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _run_message_loop(self):
        self.thread_id = kernel32.GetCurrentThreadId()
        self.hook_proc_ref = HOOKPROC(self._hook_procedure)
        self.hook_id = user32.SetWindowsHookExW(WH_MOUSE_LL, self.hook_proc_ref, None, 0)
        self.is_running = True

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.hook_id:
            user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
        self.is_running = False

    def start(self):
        if self.is_running:
            return
        self.thread = threading.Thread(target=self._run_message_loop, daemon=True)
        self.thread.start()
        time.sleep(0.1)

    def stop(self):
        if not self.is_running or not self.thread_id:
            return
        if self.in_switch_mode:
            release_key(VK_MENU)
            release_key(VK_SHIFT)
            self.in_switch_mode = False

        user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.is_running = False
