"""Private ICS calendar reader.

Only timed events whose DTSTART is strictly later than the local current
time are candidates. All-day and already-started events are ignored.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import recurring_ical_events
import requests
from icalendar import Calendar

from ..constants import DIM, MUTED, WHITE
from ..rendering.common import (
    base_image,
    image_to_jpeg,
    load_font,
    trim_text,
    wrap_text,
)

calendar_http = requests.Session()
calendar_http.headers["User-Agent"] = "Pixel-Relay/1.1"

def localize_calendar_value(
    value: Any,
) -> tuple[datetime, bool]:
    local_tz = datetime.now().astimezone().tzinfo

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=local_tz), False

        return value.astimezone(local_tz), False

    if isinstance(value, date):
        return (
            datetime.combine(
                value,
                datetime.min.time(),
                tzinfo=local_tz,
            ),
            True,
        )

    raise TypeError(
        f"Unsupported ICS date: {type(value)!r}"
    )

def fetch_next_calendar_event(
    ics_url: str,
    days_ahead: int = 90,
) -> dict[str, Any] | None:
    if not ics_url:
        raise RuntimeError(
            "The private calendar ICS URL is missing."
        )

    response = calendar_http.get(
        ics_url,
        timeout=20,
    )
    response.raise_for_status()

    calendar = Calendar.from_ical(response.content)
    now = datetime.now().astimezone()
    end_window = now + timedelta(
        days=max(1, int(days_ahead))
    )

    # Expand recurring events from the current instant forward.
    # DTSTART is validated strictly again below.
    expanded = recurring_ical_events.of(
        calendar
    ).between(
        now,
        end_window,
    )

    candidates = []

    for component in expanded:
        if (
            str(component.get("STATUS", "")).upper()
            == "CANCELLED"
        ):
            continue

        start_value = component.decoded("DTSTART")
        start, all_day = localize_calendar_value(
            start_value
        )

        # DATE-only DTSTART values represent all-day events and are excluded.
        if all_day:
            continue

        # Only events that have not started are eligible. An event starting at
        # the exact current instant is not considered future.
        if start <= now:
            continue

        if component.get("DTEND") is not None:
            end_value = component.decoded("DTEND")
            end, _ = localize_calendar_value(
                end_value
            )
        else:
            end = start + timedelta(hours=1)

        candidates.append(
            {
                "summary": (
                    str(
                        component.get(
                            "SUMMARY",
                            "Untitled event",
                        )
                    ).strip()
                    or "Untitled event"
                ),
                "location": str(
                    component.get("LOCATION", "")
                ).strip(),
                "start": start,
                "end": end,
                "all_day": False,
                "ongoing": False,
            }
        )

    if not candidates:
        return None

    # The first item is the future DTSTART closest to the current time.
    candidates.sort(
        key=lambda event: event["start"]
    )

    return candidates[0]

def calendar_date_label(
    event: dict[str, Any],
) -> str:
    start_date = event["start"].date()
    today = datetime.now().astimezone().date()

    if start_date == today:
        return "TODAY"

    if start_date == today + timedelta(days=1):
        return "TOMORROW"

    day_names = (
        "MON",
        "TUE",
        "WED",
        "THU",
        "FRI",
        "SAT",
        "SUN",
    )
    month_names = (
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
    )

    return (
        f"{day_names[event['start'].weekday()]} "
        f"{event['start'].day:02d} "
        f"{month_names[event['start'].month - 1]}"
    )

def create_calendar_slide(
    event: dict[str, Any] | None,
    config: dict[str, Any],
    error: str | None = None,
) -> bytes:
    accent = "#9b6fff"
    scale = float(config["font_scale"])
    image, draw = base_image(accent)

    header_font = load_font(13, True, scale)
    date_font = load_font(12, True, scale)
    title_font = load_font(19, True, scale)
    time_font = load_font(19, True, scale)
    location_font = load_font(10, False, scale)
    footer_font = load_font(9, False, scale)

    draw.text(
        (31, 31),
        "NEXT EVENT",
        font=header_font,
        fill=accent,
    )

    if event:
        draw.text(
            (31, 57),
            calendar_date_label(event),
            font=date_font,
            fill=MUTED,
        )

        title_lines = wrap_text(
            draw,
            event["summary"],
            title_font,
            177,
            max_lines=3,
        )

        start_y = 91
        line_height = max(
            22,
            round(23 * scale),
        )

        for index, line in enumerate(title_lines):
            draw.text(
                (
                    31,
                    start_y
                    + index * line_height,
                ),
                line,
                font=title_font,
                fill=WHITE,
                anchor="lm",
            )

        time_label = (
            f"{event['start'].strftime('%H:%M')} – "
            f"{event['end'].strftime('%H:%M')}"
        )

        draw.text(
            (31, 173),
            time_label,
            font=time_font,
            fill=accent,
            anchor="lm",
        )

        location = trim_text(
            draw,
            event.get("location")
            or "No location",
            location_font,
            177,
        )

        draw.text(
            (31, 199),
            location,
            font=location_font,
            fill=DIM,
            anchor="lm",
        )

        draw.text(
            (31, 218),
            "GOOGLE CALENDAR",
            font=footer_font,
            fill=DIM,
            anchor="lm",
        )

    else:
        draw.text(
            (31, 88),
            "NO EVENTS",
            font=load_font(
                23,
                True,
                scale,
            ),
            fill=WHITE,
            anchor="lm",
        )
        draw.text(
            (31, 124),
            "No upcoming events found",
            font=load_font(
                11,
                False,
                scale,
            ),
            fill=MUTED,
            anchor="lm",
        )

        if error:
            draw.text(
                (31, 165),
                trim_text(
                    draw,
                    error,
                    load_font(
                        9,
                        False,
                        scale,
                    ),
                    177,
                ),
                font=load_font(
                    9,
                    False,
                    scale,
                ),
                fill="#f0ba57",
                anchor="lm",
            )

    return image_to_jpeg(image)
