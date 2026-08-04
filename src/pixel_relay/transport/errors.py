"""Public exceptions raised by the transport layer."""


class PixelRelayError(RuntimeError):
    """Base exception for Pixel Relay."""


class InvalidImageError(PixelRelayError, ValueError):
    """The image payload or remote filename is invalid."""


class ImageNotFoundError(PixelRelayError, LookupError):
    """A requested remote image does not exist."""
