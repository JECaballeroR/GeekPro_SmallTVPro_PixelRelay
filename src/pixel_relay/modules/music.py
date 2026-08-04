"""Static Windows media dashboard renderer."""

from __future__ import annotations

from typing import Any

from ..constants import ACCENT, DIM, MUTED, TRACK, WHITE
from ..rendering.common import (
    base_image,
    format_duration,
    friendly_source,
    image_to_jpeg,
    load_font,
    trim_text,
    wrap_text,
)

def create_music_slide(
    media: dict[str, Any],
    config: dict[str, Any],
) -> bytes:
    scale = float(config["font_scale"])
    image, draw = base_image(ACCENT)

    header_font = load_font(12, True, scale)
    title_font = load_font(19, True, scale)
    artist_font = load_font(13, True, scale)
    album_font = load_font(11, False, scale)
    duration_label_font = load_font(9, True, scale)
    duration_font = load_font(21, True, scale)
    source_font = load_font(10, True, scale)

    draw.text(
        (31, 31),
        "PLAYING",
        font=header_font,
        fill=ACCENT,
    )

    title = str(media.get("title") or "Untitled")
    title_lines = wrap_text(
        draw,
        title,
        title_font,
        181,
        max_lines=2,
    ) or ["Untitled"]

    line_height = max(22, round(23 * scale))
    total_height = len(title_lines) * line_height

    # Keep the track title slightly lower for visual balance.
    start_y = 87 - total_height // 2

    for index, line in enumerate(title_lines):
        draw.text(
            (31, start_y + index * line_height),
            line,
            font=title_font,
            fill=WHITE,
            anchor="lm",
        )

    artist = trim_text(
        draw,
        media.get("artist") or "Unknown artist",
        artist_font,
        181,
    )
    album = trim_text(
        draw,
        media.get("album") or "",
        album_font,
        181,
    )

    draw.text(
        (31, 128),
        artist,
        font=artist_font,
        fill=MUTED,
        anchor="lm",
    )

    if album:
        draw.text(
            (31, 150),
            album,
            font=album_font,
            fill=DIM,
            anchor="lm",
        )

    duration = float(media.get("duration", 0))

    draw.text(
        (31, 176),
        "DURATION",
        font=duration_label_font,
        fill=DIM,
        anchor="lm",
    )
    draw.text(
        (31, 199),
        format_duration(duration),
        font=duration_font,
        fill=WHITE,
        anchor="lm",
    )

    source = friendly_source(media.get("raw_source", ""))
    draw.text(
        (208, 209),
        source,
        font=source_font,
        fill=DIM,
        anchor="rm",
    )

    return image_to_jpeg(image)

def create_idle_music_slide(config: dict[str, Any]) -> bytes:
    """
    Creates the initial static music image before any song has played.

    This is not a paused-state image. When playback pauses or stops, the last
    real song image remains untouched.
    """
    scale = float(config["font_scale"])
    image, draw = base_image(ACCENT)

    draw.text(
        (37, 34),
        "MUSIC",
        font=load_font(14, True, scale),
        fill=ACCENT,
    )

    draw.text(
        (121, 103),
        "WAITING",
        font=load_font(26, True, scale),
        fill=WHITE,
        anchor="mm",
    )
    draw.text(
        (121, 137),
        "FOR PLAYBACK",
        font=load_font(21, True, scale),
        fill=WHITE,
        anchor="mm",
    )

    draw.line((37, 177, 205, 177), fill=TRACK, width=2)

    draw.text(
        (121, 207),
        "WINDOWS MEDIA",
        font=load_font(11, True, scale),
        fill=DIM,
        anchor="mm",
    )

    return image_to_jpeg(image)
