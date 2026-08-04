"""High-level, device-independent image publishing API."""

from __future__ import annotations

import mimetypes
from collections.abc import Iterable, Mapping
from io import BytesIO
from pathlib import Path

from PIL import Image

from .errors import ImageNotFoundError, InvalidImageError
from .models import RemoteImage
from .protocols import ImageDisplay


class ImagePublisher:
    """Publish static images to any adapter implementing ``ImageDisplay``.

    This class is intentionally independent from the dashboard scheduler.
    It can be imported by another project to send one image, synchronize an
    album or control rotation without starting Tkinter, WinRT or the tray.
    """

    def __init__(
        self,
        device: ImageDisplay,
        *,
        managed_names: Iterable[str] = (),
    ) -> None:
        if not isinstance(device, ImageDisplay):
            raise TypeError(
                "device must implement the ImageDisplay protocol"
            )

        self.device = device
        self.managed_names = frozenset(managed_names)

    @staticmethod
    def _validate_filename(filename: str) -> str:
        candidate = filename.strip()

        if not candidate:
            raise InvalidImageError("Remote filename cannot be empty.")

        if "/" in candidate or "\\" in candidate:
            raise InvalidImageError(
                "Remote filename must not contain directory separators."
            )

        suffix = Path(candidate).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            raise InvalidImageError(
                "Supported extensions: .jpg, .jpeg, .png, .gif and .webp."
            )

        return candidate

    @staticmethod
    def _mime_type(filename: str) -> str:
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"

    def list_images(self) -> list[RemoteImage]:
        return self.device.list_images()

    def publish_bytes(
        self,
        filename: str,
        content: bytes,
        *,
        mime_type: str | None = None,
    ) -> RemoteImage:
        """Create or replace one remote image from bytes."""

        remote_name = self._validate_filename(filename)

        if not isinstance(content, bytes) or not content:
            raise InvalidImageError("Image content must be non-empty bytes.")

        resolved_mime = mime_type or self._mime_type(remote_name)
        self.device.upload_image(remote_name, content, resolved_mime)

        return RemoteImage(
            name=remote_name,
            path=f"/image/{remote_name}",
            size=str(len(content)),
        )

    def publish_file(
        self,
        path: str | Path,
        *,
        remote_name: str | None = None,
    ) -> RemoteImage:
        """Publish an image file without loading any dashboard modules."""

        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)

        return self.publish_bytes(
            remote_name or source.name,
            source.read_bytes(),
        )

    def publish_pillow(
        self,
        filename: str,
        image: Image.Image,
        *,
        quality: int = 90,
    ) -> RemoteImage:
        """Encode and publish a Pillow image.

        JPEG is used for ``.jpg``/``.jpeg`` names. PNG, GIF and WEBP use
        their matching Pillow encoders.
        """

        remote_name = self._validate_filename(filename)
        suffix = Path(remote_name).suffix.lower()

        formats = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".gif": "GIF",
            ".webp": "WEBP",
        }
        image_format = formats[suffix]

        output = BytesIO()
        save_kwargs: dict[str, object] = {}

        if image_format == "JPEG":
            image = image.convert("RGB")
            save_kwargs.update(
                quality=max(1, min(100, int(quality))),
                optimize=True,
            )

        image.save(output, image_format, **save_kwargs)
        return self.publish_bytes(
            remote_name,
            output.getvalue(),
            mime_type=self._mime_type(remote_name),
        )

    def delete(self, filename: str, *, missing_ok: bool = False) -> bool:
        """Delete an image by filename."""

        remote_name = self._validate_filename(filename)
        match = next(
            (
                image
                for image in self.list_images()
                if image.name == remote_name
            ),
            None,
        )

        if match is None:
            if missing_ok:
                return False
            raise ImageNotFoundError(remote_name)

        self.device.delete_image(match)
        return True

    def reconcile(
        self,
        keep_names: Iterable[str],
        *,
        clear_unknown: bool = False,
    ) -> list[str]:
        """Remove files outside the desired album state.

        By default only files explicitly registered in ``managed_names`` are
        removed. ``clear_unknown=True`` gives the caller exclusive ownership
        of the device album.
        """

        keep = {
            self._validate_filename(name)
            for name in keep_names
        }
        deleted: list[str] = []

        for remote in self.list_images():
            is_managed = clear_unknown or remote.name in self.managed_names
            if is_managed and remote.name not in keep:
                self.device.delete_image(remote)
                deleted.append(remote.name)

        return deleted

    def sync(
        self,
        images: Mapping[str, bytes],
        *,
        clear_unknown: bool = False,
    ) -> list[RemoteImage]:
        """Publish a complete mapping and reconcile the remaining album."""

        published = [
            self.publish_bytes(filename, content)
            for filename, content in images.items()
        ]
        self.reconcile(
            images.keys(),
            clear_unknown=clear_unknown,
        )
        return published

    def set_rotation(self, enabled: bool, interval: int) -> None:
        self.device.configure_rotation(
            bool(enabled),
            max(1, int(interval)),
        )
