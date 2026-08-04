"""Shared Pillow rendering primitives."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..constants import ACCENT, HEIGHT, WIDTH

def load_font(size: int, bold: bool = False, scale: float = 1.0):
    size = max(8, round(size * scale))

    candidates = [
        Path(
            "C:/Windows/Fonts/segoeuib.ttf"
            if bold
            else "C:/Windows/Fonts/segoeui.ttf"
        ),
        Path(
            "C:/Windows/Fonts/arialbd.ttf"
            if bold
            else "C:/Windows/Fonts/arial.ttf"
        ),
    ]

    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)

    return ImageFont.load_default()

def base_image(accent: str = ACCENT):
    image = Image.new("RGB", (WIDTH, HEIGHT), "#000000")
    draw = ImageDraw.Draw(image)

    # Render invariant: every module starts on a true-black 240×240 canvas.
    return image, draw

def text_width(draw: ImageDraw.ImageDraw, text: str, selected_font) -> int:
    box = draw.textbbox((0, 0), str(text), font=selected_font)
    return box[2] - box[0]

def trim_text(draw, text: str, selected_font, max_width: int) -> str:
    text = str(text or "").strip()

    if text_width(draw, text, selected_font) <= max_width:
        return text

    while text:
        candidate = text.rstrip() + "…"
        if text_width(draw, candidate, selected_font) <= max_width:
            return candidate
        text = text[:-1]

    return "…"

def wrap_text(draw, text: str, selected_font, max_width: int, max_lines: int):
    words = str(text or "").split()
    if not words:
        return []

    lines: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"

        if text_width(draw, candidate, selected_font) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)
            current = word
        else:
            lines.append(trim_text(draw, word, selected_font, max_width))
            current = ""

        if len(lines) >= max_lines:
            break

    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) == max_lines:
        consumed = " ".join(lines).replace("…", "")
        if len(consumed) < len(str(text).strip()):
            lines[-1] = trim_text(
                draw,
                lines[-1] + "…",
                selected_font,
                max_width,
            )

    return lines[:max_lines]

def image_to_jpeg(image: Image.Image, quality: int = 91) -> bytes:
    output = BytesIO()
    image.save(
        output,
        "JPEG",
        quality=quality,
        optimize=True,
        progressive=False,
    )
    return output.getvalue()

def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"

    return f"{minutes}:{secs:02d}"

def format_cop(value: float) -> str:
    return (
        f"{value:,.2f}"
        .replace(",", "_")
        .replace(".", ",")
        .replace("_", ".")
    )

def friendly_source(raw_source: str) -> str:
    source = str(raw_source or "")
    lowered = source.lower()

    # YouTube Music Desktop puede aparecer como un paquete com.github...
    if (
        "youtube_music" in lowered
        or "youtube-music" in lowered
        or "youtubemusic" in lowered
        or "ytmusic" in lowered
        or "ytmdesktop" in lowered
        or ("github" in lowered and "youtube" in lowered)
        or ("th_ch" in lowered and "youtube" in lowered)
    ):
        return "YouTube Music"

    mappings = (
        ("spotify", "Spotify"),
        ("musicbee", "MusicBee"),
        ("vlc", "VLC"),
        ("firefox", "Firefox"),
        ("msedge", "Microsoft Edge"),
        ("microsoftedge", "Microsoft Edge"),
        ("chrome", "Google Chrome"),
    )

    for token, label in mappings:
        if token in lowered:
            return label

    cleaned = re.split(r"[!\\/]", source)[-1]
    cleaned = cleaned.replace("_", " ").replace("-", " ").strip()

    return cleaned[:28] or "Windows Media"
