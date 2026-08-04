from io import BytesIO

from PIL import Image

from pixel_relay.config import DEFAULT_CONFIG
from pixel_relay.modules.clock import create_clock_image
from pixel_relay.modules.music import create_music_slide


def assert_jpeg_240_square(data: bytes) -> None:
    image = Image.open(BytesIO(data))
    assert image.format == "JPEG"
    assert image.size == (240, 240)


def test_clock_is_static_jpeg():
    assert_jpeg_240_square(create_clock_image(DEFAULT_CONFIG))


def test_music_is_static_jpeg():
    media = {
        "title": "Test song",
        "artist": "JECR",
        "album": "Test album",
        "duration": 245,
        "raw_source": "spotify.exe",
    }
    assert_jpeg_240_square(create_music_slide(media, DEFAULT_CONFIG))
