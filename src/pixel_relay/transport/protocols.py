"""Protocols implemented by image-capable display adapters."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import RemoteImage


@runtime_checkable
class ImageDisplay(Protocol):
    """Minimum contract required by :class:`ImagePublisher`.

    Device integrations should translate their vendor-specific API into this
    small interface. The rest of Pixel Relay never needs to know endpoint
    names, multipart field names or device-specific paths.
    """

    def list_images(self) -> list[RemoteImage]:
        """Return images currently available on the device."""

    def upload_image(
        self,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        """Create or replace one image."""

    def delete_image(self, remote: RemoteImage) -> None:
        """Delete one previously listed image."""

    def configure_rotation(self, enabled: bool, interval: int) -> None:
        """Enable or disable the device slideshow."""
