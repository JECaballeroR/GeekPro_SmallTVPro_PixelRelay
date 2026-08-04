"""Pixel Relay notification panel renderer by JECaballeroR."""

from __future__ import annotations

from typing import Any

from ..constants import MUTED, TRACK, WHITE
from ..rendering.common import (
    base_image,
    image_to_jpeg,
    load_font,
    trim_text,
    wrap_text,
)

def create_notification_slide(config: dict[str, Any]) -> bytes:
    accent = str(config["custom_accent"])
    scale = float(config["font_scale"])
    image, draw = base_image(accent)

    title_font = load_font(15, True, scale)
    body_font = load_font(20, True, scale)
    footer_font = load_font(11, False, scale)

    title = str(config["custom_title"] or "THANK YOU")
    body = str(config["custom_body"] or "Thanks for using Pixel Relay.")
    footer = str(config["custom_footer"] or "")

    draw.text(
        (37, 35),
        trim_text(draw, title.upper(), title_font, 168),
        font=title_font,
        fill=accent,
    )

    lines = wrap_text(
        draw,
        body,
        body_font,
        165,
        max_lines=4,
    )

    line_height = max(25, round(27 * scale))
    total_height = len(lines) * line_height
    start_y = 120 - total_height // 2

    for index, line in enumerate(lines):
        draw.text(
            (121, start_y + index * line_height),
            line,
            font=body_font,
            fill=WHITE,
            anchor="mm",
        )

    if footer:
        draw.line((37, 190, 205, 190), fill=TRACK)
        draw.text(
            (121, 208),
            trim_text(draw, footer, footer_font, 166),
            font=footer_font,
            fill=MUTED,
            anchor="mm",
        )

    return image_to_jpeg(image)

# Compatibility alias retained for the monitor API.
create_custom_slide = create_notification_slide
