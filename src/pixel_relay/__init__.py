"""Pixel Relay.

Modular static-image dashboard and reusable display transport by
JECaballeroR. Small-format marks use the JECR initials.
"""

from .devices import GeekMagicDevice
from .transport import (
    ImageDisplay,
    ImageNotFoundError,
    ImagePublisher,
    InvalidImageError,
    PixelRelayError,
    RemoteImage,
)

__all__ = [
    "GeekMagicDevice",
    "ImageDisplay",
    "ImageNotFoundError",
    "ImagePublisher",
    "InvalidImageError",
    "PixelRelayError",
    "RemoteImage",
    "__version__",
]

__version__ = "1.3.1"
