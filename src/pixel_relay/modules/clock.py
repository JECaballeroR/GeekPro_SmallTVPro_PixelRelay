"""Minute-resolution static clock renderer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..constants import DIM, MUTED, TRACK, WHITE
from ..rendering.common import (
    base_image,
    image_to_jpeg,
    load_font,
    trim_text,
)


DAYS_EN = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

MONTHS_EN = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def create_clock_image(config: dict[str, Any]) -> bytes:
    """Create a stable minute-only JPEG to avoid replacing an active clock GIF."""
    moment = datetime.now().astimezone()
    scale = float(config["font_scale"])
    image, draw = base_image("#ffffff")

    use_24h = bool(config["clock_24h"])
    time_format = "%H:%M" if use_24h else "%I:%M %p"
    time_text = moment.strftime(time_format)

    if not use_24h:
        time_text = time_text.lstrip("0")

    date_text = (
        f"{DAYS_EN[moment.weekday()]}, "
        f"{MONTHS_EN[moment.month - 1]} {moment.day}"
    )

    draw.text(
        (29, 30),
        "CLOCK",
        font=load_font(14, True, scale),
        fill=MUTED,
    )

    draw.text(
        (121, 103),
        time_text,
        font=load_font(52 if use_24h else 40, True, scale),
        fill=WHITE,
        anchor="mm",
    )

    draw.line((29, 148, 211, 148), fill=TRACK, width=2)

    date_font = load_font(15, True, scale)
    draw.text(
        (121, 179),
        trim_text(
            draw,
            date_text.capitalize(),
            date_font,
            190,
        ),
        font=date_font,
        fill=MUTED,
        anchor="mm",
    )

    draw.text(
        (121, 211),
        f"{str(config['weather_city']).upper()} · {str(config['weather_country_code']).upper()}",
        font=load_font(10, False, scale),
        fill=DIM,
        anchor="mm",
    )

    return image_to_jpeg(image, quality=92)
