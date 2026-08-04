"""Windows system-tray frontend.

Run with `pyw -m pixel_relay tray` to avoid a visible console window.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import config_path, load_config, runtime_log_path
from .constants import PRODUCT_FULL_NAME
from .runtime import RuntimeController


LOGGER = logging.getLogger(__name__)


def _tray_icon_image() -> Image.Image:
    image = Image.new("RGB", (64, 64), "#000000")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (3, 3, 60, 60),
        radius=10,
        outline="#1388e9",
        width=4,
    )
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    draw.text((32, 32), "JECR", font=font, fill="#ffffff", anchor="mm")
    return image


class PixelRelayTrayApp:
    def __init__(self) -> None:
        # Importing pystray here keeps headless mode independent from tray
        # backend initialization.
        import pystray

        self.pystray = pystray
        self.controller = RuntimeController(load_config())
        self._closing = threading.Event()

        self.icon = pystray.Icon(
            "pixel_relay",
            _tray_icon_image(),
            PRODUCT_FULL_NAME,
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Start / play",
                    self._start,
                    enabled=lambda _item: not self.controller.is_running,
                    default=True,
                ),
                pystray.MenuItem(
                    "Stop",
                    self._stop,
                    enabled=lambda _item: self.controller.is_running,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Pause rotation",
                    lambda _icon, _item: self.controller.command(
                        "pause_rotation"
                    ),
                ),
                pystray.MenuItem(
                    "Resume rotation",
                    lambda _icon, _item: self.controller.command(
                        "resume_rotation"
                    ),
                ),
                pystray.MenuItem(
                    "Show music now",
                    lambda _icon, _item: self.controller.command(
                        "focus_music"
                    ),
                ),
                pystray.MenuItem(
                    "Rebuild gallery",
                    lambda _icon, _item: self.controller.command(
                        "rebuild_gallery"
                    ),
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Open settings",
                    self._open_gui,
                ),
                pystray.MenuItem(
                    "Open configuration folder",
                    self._open_config_folder,
                ),
                pystray.MenuItem("Exit", self._quit),
            ),
        )

    def _start(self, _icon=None, _item=None) -> None:
        # Reload disk/.env configuration before each restart so edits made in
        # the GUI become effective without restarting the tray process.
        self.controller.config = load_config()

        if self.controller.start():
            self.icon.notify(
                "Monitor started.",
                PRODUCT_FULL_NAME,
            )

    def _stop(self, _icon=None, _item=None) -> None:
        if self.controller.stop():
            self.icon.notify(
                "Monitor stopped.",
                PRODUCT_FULL_NAME,
            )

    def _open_gui(self, _icon=None, _item=None) -> None:
        # Do not run two upload schedulers against the same album. The tray
        # monitor is stopped before the independent Tk process is opened.
        self.controller.stop(wait=True, timeout=3.0)

        # A separate process is deliberate: Tk must own the main thread and
        # pystray must keep its own message loop responsive.
        subprocess.Popen(
            [sys.executable, "-m", "pixel_relay", "gui"],
            close_fds=True,
        )

    def _open_config_folder(self, _icon=None, _item=None) -> None:
        path = config_path().parent
        path.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["explorer", str(path)])

    def _drain_logs(self) -> None:
        while not self._closing.is_set():
            try:
                kind, message = self.controller.log_queue.get(timeout=0.5)
                LOGGER.info("%s: %s", kind, message)
                if kind == "status":
                    self.icon.title = f"Pixel Relay · {message}"
            except queue.Empty:
                continue
            except Exception:
                LOGGER.exception("Error processing tray status")

    def _quit(self, _icon=None, _item=None) -> None:
        self._closing.set()
        self.controller.stop(wait=True, timeout=3.0)
        self.icon.stop()

    def run(self) -> None:
        log_file = runtime_log_path()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )

        LOGGER.setLevel(logging.INFO)
        LOGGER.addHandler(handler)
        LOGGER.propagate = False

        threading.Thread(
            target=self._drain_logs,
            name="PixelRelayTrayLogs",
            daemon=True,
        ).start()

        if bool(self.controller.config.get("tray_autostart", True)):
            self.controller.start()

        self.icon.run()


def run_tray() -> None:
    PixelRelayTrayApp().run()
