"""Windows Global System Media Transport Controls adapter.

WinRT imports are lazy so configuration commands and documentation can be
used without initializing Windows media APIs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


async def request_media_manager():
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    )
    return await MediaManager.request_async()

def timedelta_seconds(value) -> float:
    try:
        return float(value.total_seconds())
    except Exception:
        return 0.0

async def read_windows_media(manager) -> dict[str, Any]:
    from winrt.windows.media.control import (
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
    )
    current_session = manager.get_current_session()

    if current_session is None:
        return {
            "playing": False,
            "title": "",
            "artist": "",
            "album": "",
            "raw_source": "",
            "position": 0.0,
            "duration": 0.0,
            "rate": 1.0,
        }

    playback_info = current_session.get_playback_info()
    playing = (
        playback_info.playback_status
        == PlaybackStatus.PLAYING
    )

    timeline = current_session.get_timeline_properties()
    start = timedelta_seconds(timeline.start_time)
    end = timedelta_seconds(timeline.end_time)
    position = max(
        0.0,
        timedelta_seconds(timeline.position) - start,
    )
    duration = max(0.0, end - start)
    rate = float(playback_info.playback_rate or 1.0)

    if playing:
        try:
            last_update = timeline.last_updated_time

            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=timezone.utc)

            position += max(
                0.0,
                (
                    datetime.now(timezone.utc)
                    - last_update
                ).total_seconds(),
            ) * rate
        except Exception:
            pass

    if duration > 0:
        position = min(position, duration)

    try:
        properties = (
            await current_session.try_get_media_properties_async()
        )
    except Exception:
        properties = None

    raw_source = str(
        current_session.source_app_user_model_id
        or ""
    )

    return {
        "playing": playing,
        "title": (
            str(properties.title or "")
            if properties
            else raw_source
        ),
        "artist": (
            str(properties.artist or "")
            if properties
            else ""
        ),
        "album": (
            str(properties.album_title or "")
            if properties
            else ""
        ),
        "raw_source": raw_source,
        "position": position,
        "duration": duration,
        "rate": rate,
    }

def media_identity(media: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        media.get("raw_source", ""),
        media.get("title", ""),
        media.get("artist", ""),
        media.get("album", ""),
    )
