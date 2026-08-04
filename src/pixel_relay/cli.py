"""Command-line entry point for Pixel Relay."""

from __future__ import annotations

import argparse
import queue
import signal
from pathlib import Path

from .config import config_path, load_config
from .constants import PRODUCT_FULL_NAME


def _run_headless() -> int:
    from .runtime import RuntimeController

    controller = RuntimeController(load_config())

    def request_stop(*_args) -> None:
        controller.stop()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    controller.start()
    print(
        f"{PRODUCT_FULL_NAME} is running without a window. "
        "Press Ctrl+C to stop.",
        flush=True,
    )

    try:
        while controller.is_running:
            try:
                kind, message = controller.log_queue.get(timeout=0.5)
                print(f"[{kind.upper()}] {message}", flush=True)
            except queue.Empty:
                continue
    finally:
        controller.stop(wait=True, timeout=5.0)

    return 0


def _send_image(
    path: Path,
    *,
    host: str | None,
    remote_name: str | None,
) -> int:
    from .devices import GeekMagicDevice
    from .transport import ImagePublisher

    config = load_config()
    device = GeekMagicDevice(
        host or str(config["device_ip"]),
        int(config["request_timeout"]),
    )
    publisher = ImagePublisher(device)
    published = publisher.publish_file(path, remote_name=remote_name)
    print(f"Sent: {published.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pixel-relay",
        description=(
            "Pixel Relay · modular display transport by JECaballeroR"
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("gui", help="Open the Tkinter interface.")
    subparsers.add_parser("headless", help="Run without a window.")
    subparsers.add_parser("tray", help="Run in the Windows system tray.")
    subparsers.add_parser(
        "config-path",
        help="Print the local configuration path.",
    )

    send = subparsers.add_parser(
        "send",
        help="Send one image without starting the dashboard.",
    )
    send.add_argument("path", type=Path)
    send.add_argument(
        "--host",
        help="Device IP or URL. Uses .env when omitted.",
    )
    send.add_argument(
        "--name",
        dest="remote_name",
        help="Remote name, for example 50_demo.jpg.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "gui"

    if command == "gui":
        from .ui import run_gui
        run_gui()
        return 0

    if command == "tray":
        from .tray import run_tray
        run_tray()
        return 0

    if command == "headless":
        return _run_headless()

    if command == "send":
        return _send_image(
            args.path,
            host=args.host,
            remote_name=args.remote_name,
        )

    print(config_path())
    return 0
