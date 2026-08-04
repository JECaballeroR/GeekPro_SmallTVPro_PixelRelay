"""Shared visual and device-file constants.

Keeping filenames centralized is important because the SmallTV Pro album
behaves as an ordered slideshow. Renaming a file changes both ordering and
the cleanup contract with existing installations.
"""

PRODUCT_NAME = "Pixel Relay"
PRODUCT_AUTHOR = "JECaballeroR"
PRODUCT_BYLINE = f"by {PRODUCT_AUTHOR}"
PRODUCT_FULL_NAME = f"{PRODUCT_NAME} {PRODUCT_BYLINE}"
PRODUCT_SHORT_MARK = "JECR"

WIDTH = 240
HEIGHT = 240

BACKGROUND = "#000000"
ACCENT = "#1388e9"
WHITE = "#ffffff"
MUTED = "#bdc4d0"
DIM = "#8294aa"
TRACK = "#242424"

MUSIC_FILE = "00_music.jpg"
FX_FILE = "10_usdcop.jpg"
WEATHER_FILE = "20_weather.jpg"
CALENDAR_FILE = "25_calendar.jpg"
NOTIFICATIONS_FILE = "30_notifications.jpg"
CLOCK_FILE = "40_clock.jpg"

# Files produced by earlier prototypes. They remain managed so upgrades can
# remove stale images without requiring a factory reset.
LEGACY_CLOCK_FILE = "40_clock.gif"
LEGACY_CUSTOM_FILE = "30_custom.jpg"

FILE_ORDER = (
    MUSIC_FILE,
    FX_FILE,
    WEATHER_FILE,
    CALENDAR_FILE,
    NOTIFICATIONS_FILE,
    CLOCK_FILE,
)

MANAGED_FILES = set(FILE_ORDER) | {
    LEGACY_CLOCK_FILE,
    LEGACY_CUSTOM_FILE,
}

MODULE_FILES = {
    "music_enabled": MUSIC_FILE,
    "fx_enabled": FX_FILE,
    "weather_enabled": WEATHER_FILE,
    "calendar_enabled": CALENDAR_FILE,
    "custom_enabled": NOTIFICATIONS_FILE,
    "clock_enabled": CLOCK_FILE,
}
