import pystray
from PIL import Image, ImageDraw

def create_tray_icon_image(active=True):
    """Draw a clean, modern mouse icon."""
    size = (64, 64)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    body_color = "#2563EB" if active else "#64748B"  # Blue if active, Slate Gray if paused
    accent_color = "#38BDF8" if active else "#94A3B8"
    wheel_color = "#FFFFFF"

    # Outer mouse body
    draw.rounded_rectangle([12, 6, 52, 58], radius=18, fill=body_color)

    # Accent outline / highlight
    draw.rounded_rectangle([15, 9, 49, 55], radius=15, outline=accent_color, width=2)

    # Mouse wheel divider and wheel
    draw.line([32, 8, 32, 28], fill="#1E293B", width=2)
    draw.rounded_rectangle([28, 14, 36, 26], radius=4, fill=wheel_color)

    return image

class TrayIconManager:
    def __init__(self, on_show, on_toggle_engine, on_exit, get_engine_state):
        self.on_show = on_show
        self.on_toggle_engine = on_toggle_engine
        self.on_exit = on_exit
        self.get_engine_state = get_engine_state
        self.icon = None

    def _get_engine_label(self, item):
        active = self.get_engine_state()
        return "Pause Engine (Active)" if active else "Resume Engine (Paused)"

    def setup(self):
        menu = pystray.Menu(
            pystray.MenuItem("Open Settings", self.on_show, default=True),
            pystray.MenuItem(self._get_engine_label, self.on_toggle_engine),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.on_exit)
        )

        image = create_tray_icon_image(self.get_engine_state())
        self.icon = pystray.Icon(
            name="MouseCustomizer",
            icon=image,
            title="Mouse Customizer",
            menu=menu
        )

    def start(self):
        if not self.icon:
            self.setup()
        self.icon.run_detached()

    def update_icon(self):
        if self.icon:
            active = self.get_engine_state()
            self.icon.icon = create_tray_icon_image(active)
            self.icon.update_menu()

    def stop(self):
        if self.icon:
            try:
                self.icon.stop()
            except Exception:
                pass
