"""Long-running dashboard orchestration service.

Data retrieval and rendering live in independent modules. This class owns
scheduling, cache consistency, device uploads and album state only.
"""

from __future__ import annotations

import asyncio
import queue
import threading
import time
import traceback
from datetime import datetime
from typing import Any

from .constants import (
    CALENDAR_FILE,
    CLOCK_FILE,
    FILE_ORDER,
    FX_FILE,
    LEGACY_CLOCK_FILE,
    MANAGED_FILES,
    MUSIC_FILE,
    NOTIFICATIONS_FILE,
    WEATHER_FILE,
)
from .devices import GeekMagicDevice
from .transport import ImagePublisher
from .media.windows import (
    media_identity,
    read_windows_media,
    request_media_manager,
)
from .modules.calendar import (
    create_calendar_slide,
    fetch_next_calendar_event,
)
from .modules.clock import create_clock_image
from .modules.fx import create_fx_slide, fetch_fx_data
from .modules.music import create_idle_music_slide, create_music_slide
from .modules.notifications import create_custom_slide
from .modules.weather import create_weather_slide, fetch_weather_no_key
from .rendering.common import format_cop, friendly_source

class DashboardMonitor:
    def __init__(
        self,
        config: dict[str, Any],
        stop_event: threading.Event,
        log_queue: queue.Queue,
        config_queue: queue.Queue,
        command_queue: queue.Queue,
    ):
        self.config = dict(config)
        self.stop_event = stop_event
        self.log_queue = log_queue
        self.config_queue = config_queue
        self.command_queue = command_queue

        self.device = GeekMagicDevice(
            str(self.config["device_ip"]),
            int(self.config["request_timeout"]),
        )
        self.publisher = ImagePublisher(
            self.device,
            managed_names=MANAGED_FILES,
        )

        self.last_media_identity = None
        self.last_music_upload = 0.0
        self.last_fx_update = 0.0
        self.last_weather_update = 0.0
        self.last_calendar_update = 0.0
        self.last_clock_update = 0.0
        self.last_clock_minute: str | None = None
        self.fx_data = None
        self.weather_data = None
        self.calendar_data = None
        self.force_sync = True

        # Last generated version of each file. This allows the album to be
        # rebuilt without re-fetching data or losing the other modules.
        self.content_cache: dict[str, bytes] = {}

        # Rotation controller state.
        self.rotation_state: bool | None = None
        self.rotation_override: bool | None = None
        self.music_focus_active = False
        self.music_focus_until = 0.0
        self.last_playing = False

    def log(self, message: str):
        self.log_queue.put(("log", message))

    def status(self, message: str):
        self.log_queue.put(("status", message))

    def apply_pending_config(self):
        latest = None

        try:
            while True:
                latest = self.config_queue.get_nowait()
        except queue.Empty:
            pass

        if latest is None:
            return

        old_signature = (
            str(self.config["device_ip"]),
            int(self.config["request_timeout"]),
        )
        new_signature = (
            str(latest["device_ip"]),
            int(latest["request_timeout"]),
        )

        self.config = dict(latest)
        self.force_sync = True
        self.rotation_override = None
        self.rotation_state = None

        if old_signature != new_signature:
            self.device = GeekMagicDevice(*new_signature)
            self.publisher = ImagePublisher(
                self.device,
                managed_names=MANAGED_FILES,
            )

        self.log("Configuration applied; the selected automatic mode will be used.")

    def enabled_files(self) -> set[str]:
        files: set[str] = set()

        if bool(self.config["music_enabled"]):
            files.add(MUSIC_FILE)
        if bool(self.config["fx_enabled"]):
            files.add(FX_FILE)
        if bool(self.config["weather_enabled"]):
            files.add(WEATHER_FILE)
        if bool(self.config["calendar_enabled"]):
            files.add(CALENDAR_FILE)
        if bool(self.config["custom_enabled"]):
            files.add(NOTIFICATIONS_FILE)
        if bool(self.config["clock_enabled"]):
            files.add(CLOCK_FILE)

        return files

    def enabled_files_ordered(self) -> list[str]:
        enabled = self.enabled_files()
        return [filename for filename in FILE_ORDER if filename in enabled]

    def automatic_rotation_desired(self, media_playing: bool) -> bool:
        if self.rotation_override is not None:
            return self.rotation_override

        if not bool(self.config["auto_rotation_enabled"]):
            return False

        if media_playing and not bool(self.config["rotate_while_playing"]):
            return False

        return True

    async def set_rotation(self, enabled: bool, reason: str, force: bool = False):
        if self.music_focus_active and enabled:
            return

        if self.rotation_state == enabled and not force:
            return

        interval = max(1, int(self.config["rotation_seconds"]))

        try:
            await asyncio.to_thread(
                self.publisher.set_rotation,
                enabled,
                interval,
            )
            self.rotation_state = enabled
            self.log(
                ("Rotation enabled" if enabled else "Rotation paused")
                + f" ({reason})."
            )
        except Exception as error:
            self.log(f"Could not control rotation: {error}")

    async def reconcile_files(self):
        keep = self.enabled_files()

        await asyncio.to_thread(
            self.publisher.reconcile,
            keep,
            clear_unknown=bool(self.config["clear_unknown_files"]),
        )

        if bool(self.config["music_enabled"]):
            try:
                idle_content = create_idle_music_slide(self.config)
                self.content_cache.setdefault(MUSIC_FILE, idle_content)

                existing_names = {
                    item.name
                    for item in await asyncio.to_thread(
                        self.publisher.list_images
                    )
                }

                if MUSIC_FILE not in existing_names:
                    await asyncio.to_thread(
                        self.publisher.publish_bytes,
                        MUSIC_FILE,
                        idle_content,
                    )
                    self.log("Initial music image created.")
            except Exception as error:
                self.log(f"Could not create the initial music image: {error}")

    async def focus_music(self, reason: str):
        """Select the music card using the stock Picture album endpoints.

        When pause-on-focus is enabled, the image request sends
        ``album_autoplay=0`` and the slideshow request sends
        ``gif_loop=1&i_i=<seconds>&autoplay=0``. Otherwise Pixel Relay only
        changes ``album_path`` and leaves autoplay untouched.
        """

        if not bool(self.config["music_enabled"]):
            return

        if MUSIC_FILE not in self.content_cache:
            self.log("No music image is available to focus.")
            return

        pause_autoplay = bool(
            self.config["music_pause_autoplay_on_focus"]
        )

        await asyncio.to_thread(
            self.publisher.select_image,
            MUSIC_FILE,
            autoplay=False if pause_autoplay else None,
        )

        self.status(f"Music focus · {reason}")

        if not pause_autoplay:
            self.music_focus_active = False
            self.music_focus_until = 0.0
            self.log(
                "Music selected directly; album autoplay was left unchanged."
            )
            return

        self.music_focus_active = True
        self.music_focus_until = (
            time.monotonic()
            + max(1, int(self.config["music_focus_seconds"]))
        )

        # ``i_i`` remains the configured seconds-per-image value even while
        # autoplay is paused, matching the stock web UX request.
        await self.set_rotation(False, "music focus", force=True)

        self.log(
            "Music selected and autoplay paused; "
            f"rotation will resume in {int(self.config['music_focus_seconds'])} s."
        )

    async def finish_music_focus_if_needed(self, media_playing: bool):
        if not self.music_focus_active:
            await self.set_rotation(
                self.automatic_rotation_desired(media_playing),
                "normal mode",
            )
            return

        if not media_playing:
            self.music_focus_active = False
            self.music_focus_until = 0.0
            self.status("Active · rotating panels")
            await self.set_rotation(
                self.automatic_rotation_desired(False),
                "music paused or stopped",
                force=True,
            )
            return

        if time.monotonic() >= self.music_focus_until:
            self.music_focus_active = False
            self.music_focus_until = 0.0
            self.status("Active · music and panels")
            await self.set_rotation(
                self.automatic_rotation_desired(True),
                "end of music focus",
                force=True,
            )

    async def process_commands(self, media_playing: bool):
        commands: list[tuple[str, Any]] = []

        try:
            while True:
                commands.append(self.command_queue.get_nowait())
        except queue.Empty:
            pass

        for command, payload in commands:
            if command == "pause_rotation":
                self.rotation_override = False
                self.music_focus_active = False
                await self.set_rotation(False, "control manual", force=True)

            elif command == "resume_rotation":
                self.rotation_override = True
                self.music_focus_active = False
                await self.set_rotation(True, "control manual", force=True)

            elif command == "follow_config":
                self.rotation_override = None
                self.music_focus_active = False
                await self.set_rotation(
                    self.automatic_rotation_desired(media_playing),
                    "automatic settings",
                    force=True,
                )

            elif command == "focus_music":
                await self.focus_music("control manual")

            elif command == "rebuild_gallery":
                self.force_sync = True
                self.log("Full gallery rebuild requested.")

    async def update_music(
        self,
        media: dict[str, Any],
        force: bool,
    ) -> bool:
        if not bool(self.config["music_enabled"]):
            return False

        if not media["playing"]:
            return False

        identity_changed = (
            media_identity(media)
            != self.last_media_identity
        )
        needs_initial = MUSIC_FILE not in self.content_cache

        if not (force or identity_changed or needs_initial):
            return False

        image_data = await asyncio.to_thread(
            create_music_slide,
            media,
            self.config,
        )
        self.content_cache[MUSIC_FILE] = image_data

        await asyncio.to_thread(
            self.publisher.publish_bytes,
            MUSIC_FILE,
            image_data,
        )

        self.last_media_identity = media_identity(media)
        self.last_music_upload = time.monotonic()

        self.log(
            "Music updated: "
            f"{media.get('title', '')} — {media.get('artist', '')} "
            f"[{friendly_source(media.get('raw_source', ''))}]"
        )

        return identity_changed

    async def update_fx(self, force: bool):
        if not bool(self.config["fx_enabled"]):
            return

        now = time.monotonic()
        if not (
            force
            or self.fx_data is None
            or now - self.last_fx_update
            >= int(self.config["fx_refresh_seconds"])
        ):
            return

        try:
            self.fx_data = await asyncio.to_thread(
                fetch_fx_data,
                str(self.config["yahoo_symbol"]),
                int(self.config["fx_history_days"]),
            )
            content = create_fx_slide(self.fx_data, self.config)
            self.last_fx_update = now
            self.log(
                "Exchange rate updated: "
                + format_cop(self.fx_data["price"])
            )
        except Exception as error:
            self.log(str(error))

            if self.fx_data is not None:
                return

            content = create_fx_slide(
                None,
                self.config,
                error=str(error),
            )

        self.content_cache[FX_FILE] = content
        await asyncio.to_thread(self.publisher.publish_bytes, FX_FILE, content)

    async def update_weather(self, force: bool):
        if not bool(self.config["weather_enabled"]):
            return

        now = time.monotonic()
        if not (
            force
            or self.weather_data is None
            or now - self.last_weather_update
            >= int(self.config["weather_refresh_seconds"])
        ):
            return

        try:
            self.weather_data = await asyncio.to_thread(
                fetch_weather_no_key,
                str(self.config["weather_city"]),
                str(self.config["weather_country_code"]),
            )
            content = create_weather_slide(
                self.weather_data,
                self.config,
            )
            self.last_weather_update = now
            self.log(
                "Weather updated: "
                f"{self.weather_data['temperature']:.0f} °C, "
                f"{self.weather_data['description']}."
            )
        except Exception as error:
            self.log(f"Weather: {error}")

            if self.weather_data is not None:
                return

            content = create_weather_slide(
                None,
                self.config,
                error=str(error),
            )

        self.content_cache[WEATHER_FILE] = content
        await asyncio.to_thread(self.publisher.publish_bytes, WEATHER_FILE, content)


    async def update_calendar(
        self,
        force: bool,
    ):
        if not bool(
            self.config["calendar_enabled"]
        ):
            return

        now = time.monotonic()

        if not (
            force
            or self.calendar_data is None
            or now - self.last_calendar_update
            >= int(
                self.config[
                    "calendar_refresh_seconds"
                ]
            )
        ):
            return

        try:
            self.calendar_data = (
                await asyncio.to_thread(
                    fetch_next_calendar_event,
                    str(
                        self.config[
                            "calendar_ics_url"
                        ]
                    ),
                    int(
                        self.config[
                            "calendar_days_ahead"
                        ]
                    ),
                )
            )

            content = create_calendar_slide(
                self.calendar_data,
                self.config,
            )
            self.last_calendar_update = now

            if self.calendar_data:
                self.log(
                    "Next event: "
                    + self.calendar_data["summary"]
                    + " · "
                    + self.calendar_data["start"].strftime(
                        "%Y-%m-%d %H:%M %Z"
                    )
                )
            else:
                self.log(
                    "Calendar updated: no upcoming events."
                )

        except Exception as error:
            self.log(
                f"Calendar: {error}"
            )

            if self.calendar_data is not None:
                return

            content = create_calendar_slide(
                None,
                self.config,
                error=str(error),
            )

        self.content_cache[
            CALENDAR_FILE
        ] = content

        await asyncio.to_thread(
            self.publisher.publish_bytes,
            CALENDAR_FILE,
            content,
        )
    async def update_clock(self, force: bool):
        if not bool(self.config["clock_enabled"]):
            return

        # The clock is a static HH:MM JPEG. It is replaced only when the minute
        # changes or the user forces a synchronization.
        current_minute = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")

        if not force and getattr(self, "last_clock_minute", None) == current_minute:
            return

        content = await asyncio.to_thread(
            create_clock_image,
            self.config,
        )
        self.content_cache[CLOCK_FILE] = content
        await asyncio.to_thread(self.publisher.publish_bytes, CLOCK_FILE, content)

        # Remove the legacy GIF without touching other images.
        try:
            for item in await asyncio.to_thread(self.publisher.list_images):
                if item.name == LEGACY_CLOCK_FILE:
                    await asyncio.to_thread(
                        self.device.delete_image,
                        item,
                    )
        except Exception as error:
            self.log(f"Could not remove the legacy clock: {error}")

        self.last_clock_minute = current_minute
        self.last_clock_update = time.monotonic()
        self.log(f"Clock updated: {datetime.now().strftime('%H:%M')}.")

    async def update_custom(self, force: bool):
        if not bool(self.config["custom_enabled"]):
            return

        if not force:
            return

        content = create_custom_slide(self.config)
        self.content_cache[NOTIFICATIONS_FILE] = content
        await asyncio.to_thread(self.publisher.publish_bytes, NOTIFICATIONS_FILE, content)
        self.log("Pixel Relay notification panel updated.")

    async def run_async(self):
        manager = await request_media_manager()
        self.log("Monitor started.")
        self.status("Active · preparing gallery")

        media = {
            "playing": False,
            "title": "",
            "artist": "",
            "album": "",
            "raw_source": "",
            "position": 0.0,
            "duration": 0.0,
            "rate": 1.0,
        }

        while not self.stop_event.is_set():
            iteration_start = time.monotonic()
            self.apply_pending_config()
            force = self.force_sync

            try:
                if force:
                    await self.reconcile_files()

                try:
                    media = await read_windows_media(manager)
                except Exception:
                    manager = await request_media_manager()
                    media = await read_windows_media(manager)

                results = await asyncio.gather(
                    self.update_music(media, force),
                    self.update_fx(force),
                    self.update_weather(force),
                    self.update_calendar(force),
                    self.update_clock(force),
                    self.update_custom(force),
                )

                song_changed = bool(results[0])

                if (
                    song_changed
                    and bool(self.config["music_focus_on_change"])
                ):
                    await self.focus_music("track changed")

                await self.process_commands(media["playing"])
                await self.finish_music_focus_if_needed(media["playing"])

                if not self.music_focus_active:
                    if media["playing"]:
                        self.status("Active · music and panels")
                    else:
                        self.status("Active · rotating panels")

                self.last_playing = media["playing"]
                self.force_sync = False

            except Exception as error:
                self.log(f"Monitor error: {error}")

            elapsed = time.monotonic() - iteration_start
            await asyncio.sleep(
                max(
                    0.05,
                    float(self.config["poll_seconds"]) - elapsed,
                )
            )

        self.status("Stopped")
        self.log("Monitor stopped.")

    def run(self):
        try:
            asyncio.run(self.run_async())
        except Exception:
            self.log(traceback.format_exc())
            self.status("Error")
