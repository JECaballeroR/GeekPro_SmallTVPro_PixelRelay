"""Process-level lifecycle controller for the dashboard monitor."""

from __future__ import annotations

import queue
import threading
from typing import Any

from .config import load_config
from .monitor import DashboardMonitor


class RuntimeController:
    """Owns monitor queues and makes start/stop idempotent.

    Tkinter, the system tray and the headless CLI all need the same lifecycle
    semantics. Centralizing them prevents each frontend from inventing a
    slightly different threading model.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = dict(config or load_config())
        self.log_queue: queue.Queue = queue.Queue()
        self.config_queue: queue.Queue = queue.Queue()
        self.command_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.monitor: DashboardMonitor | None = None
        self.thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return bool(self.thread and self.thread.is_alive())

    def start(self) -> bool:
        if self.is_running:
            return False

        self.stop_event = threading.Event()
        self.monitor = DashboardMonitor(
            self.config,
            self.stop_event,
            self.log_queue,
            self.config_queue,
            self.command_queue,
        )
        self.thread = threading.Thread(
            target=self.monitor.run,
            name="PixelRelayMonitor",
            daemon=True,
        )
        self.thread.start()
        return True

    def stop(
        self,
        *,
        wait: bool = False,
        timeout: float = 5.0,
    ) -> bool:
        if not self.is_running:
            return False

        self.stop_event.set()

        if wait and self.thread is not None:
            self.thread.join(timeout=max(0.0, timeout))

        return True

    def update_config(self, config: dict[str, Any]) -> None:
        self.config = dict(config)
        self.config_queue.put(dict(config))

    def command(self, name: str, payload: Any = None) -> None:
        if self.is_running:
            self.command_queue.put((name, payload))
