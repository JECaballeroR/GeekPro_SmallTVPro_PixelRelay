"""Configuration loading and persistence.

Precedence is deliberate:

1. built-in safe defaults;
2. local JSON written by the GUI;
3. environment variables / `.env`.

Environment variables win so headless deployments remain deterministic.
Secrets such as the private ICS URL never need to be committed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from dotenv import find_dotenv, load_dotenv


APP_NAME = "PixelRelay"


DEFAULT_CONFIG: dict[str, Any] = {
    # Device
    "device_ip": "192.168.1.63",
    "request_timeout": 25,
    "clear_unknown_files": True,

    # Album control
    "auto_rotation_enabled": True,
    "rotation_seconds": 5,
    "music_focus_on_change": True,
    "music_focus_seconds": 10,
    "rotate_while_playing": True,

    # Modules
    "music_enabled": True,
    "fx_enabled": True,
    "weather_enabled": True,
    "calendar_enabled": True,
    "clock_enabled": True,
    "custom_enabled": True,

    # Music
    "poll_seconds": 1.0,
    "font_scale": 1.18,

    # USD/COP
    "yahoo_symbol": "USDCOP=X",
    "fx_refresh_seconds": 300,
    "fx_history_days": 30,
    "show_fx_plot": True,

    # Weather
    "weather_city": "Rovaniemi",
    "weather_country_code": "FI",
    "weather_refresh_seconds": 300,

    # Calendar. Intentionally empty: private ICS URLs are secrets.
    "calendar_ics_url": "",
    "calendar_refresh_seconds": 300,
    "calendar_days_ahead": 90,

    # Clock
    "clock_refresh_seconds": 60,
    "clock_24h": True,

    # Pixel Relay notification panel defaults
    "custom_title": "THANK YOU",
    "custom_body": "Thanks for using Pixel Relay.",
    "custom_footer": "JECR",
    "custom_accent": "#1388e9",

    # Tray
    "tray_autostart": True,
}


def _as_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean: {value!r}")


def _as_text(value: str) -> str:
    # Allows a multi-line notification body in a one-line .env entry.
    return value.replace(r"\n", "\n")


ENV_FIELDS: dict[str, tuple[str, Callable[[str], Any]]] = {
    "PIXEL_DEVICE_IP": ("device_ip", str),
    "PIXEL_REQUEST_TIMEOUT": ("request_timeout", int),
    "PIXEL_CLEAR_UNKNOWN_FILES": ("clear_unknown_files", _as_bool),
    "PIXEL_AUTO_ROTATION_ENABLED": ("auto_rotation_enabled", _as_bool),
    "PIXEL_ROTATION_SECONDS": ("rotation_seconds", int),
    "PIXEL_MUSIC_FOCUS_ON_CHANGE": ("music_focus_on_change", _as_bool),
    "PIXEL_MUSIC_FOCUS_SECONDS": ("music_focus_seconds", int),
    "PIXEL_ROTATE_WHILE_PLAYING": ("rotate_while_playing", _as_bool),
    "PIXEL_MUSIC_ENABLED": ("music_enabled", _as_bool),
    "PIXEL_FX_ENABLED": ("fx_enabled", _as_bool),
    "PIXEL_WEATHER_ENABLED": ("weather_enabled", _as_bool),
    "PIXEL_CALENDAR_ENABLED": ("calendar_enabled", _as_bool),
    "PIXEL_CLOCK_ENABLED": ("clock_enabled", _as_bool),
    "PIXEL_NOTIFICATIONS_ENABLED": ("custom_enabled", _as_bool),
    "PIXEL_POLL_SECONDS": ("poll_seconds", float),
    "PIXEL_FONT_SCALE": ("font_scale", float),
    "PIXEL_YAHOO_SYMBOL": ("yahoo_symbol", str),
    "PIXEL_FX_REFRESH_SECONDS": ("fx_refresh_seconds", int),
    "PIXEL_FX_HISTORY_DAYS": ("fx_history_days", int),
    "PIXEL_SHOW_FX_PLOT": ("show_fx_plot", _as_bool),
    "PIXEL_WEATHER_CITY": ("weather_city", str),
    "PIXEL_WEATHER_COUNTRY_CODE": ("weather_country_code", str),
    "PIXEL_WEATHER_REFRESH_SECONDS": ("weather_refresh_seconds", int),
    "PIXEL_CALENDAR_ICS_URL": ("calendar_ics_url", str),
    "PIXEL_CALENDAR_REFRESH_SECONDS": ("calendar_refresh_seconds", int),
    "PIXEL_CALENDAR_DAYS_AHEAD": ("calendar_days_ahead", int),
    "PIXEL_CLOCK_24H": ("clock_24h", _as_bool),
    "PIXEL_NOTIFICATION_TITLE": ("custom_title", _as_text),
    "PIXEL_NOTIFICATION_BODY": ("custom_body", _as_text),
    "PIXEL_NOTIFICATION_FOOTER": ("custom_footer", _as_text),
    "PIXEL_NOTIFICATION_ACCENT": ("custom_accent", str),
    "PIXEL_TRAY_AUTOSTART": ("tray_autostart", _as_bool),
}


def config_path() -> Path:
    explicit = os.getenv("PIXEL_CONFIG_FILE")
    if explicit:
        return Path(explicit).expanduser().resolve()

    appdata = os.getenv("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / APP_NAME / "config.json"


def runtime_log_path() -> Path:
    """Return a writable, machine-local log path outside the repository."""
    explicit = os.getenv("PIXEL_LOG_FILE")
    if explicit:
        return Path(explicit).expanduser().resolve()

    return config_path().parent / "logs" / "pixel-relay.log"


def load_config() -> dict[str, Any]:
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)

    config = dict(DEFAULT_CONFIG)
    path = config_path()

    if path.exists():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                config.update(saved)
        except (OSError, json.JSONDecodeError):
            # A malformed local config must not prevent the tray/headless
            # process from starting; the GUI can overwrite it later.
            pass

    for env_name, (config_name, parser) in ENV_FIELDS.items():
        raw = os.getenv(env_name)
        if raw is None or raw == "":
            continue
        try:
            config[config_name] = parser(raw)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid value for {env_name}: {raw!r}"
            ) from error

    return config


def save_config(config: dict[str, Any]) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


# Compatibility aliases used by the original Tkinter class.
load_saved_config = load_config
