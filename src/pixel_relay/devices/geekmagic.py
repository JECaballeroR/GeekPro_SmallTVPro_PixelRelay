"""GeekMagic SmallTV adapter for the generic Pixel Relay transport."""

from __future__ import annotations

import re
import time
from typing import Any

import requests

from ..transport import RemoteImage


class GeekMagicDevice:
    """Translate the stock GeekMagic HTTP API into ``ImageDisplay``.

    Vendor-specific endpoint and response handling stays here. Application
    modules should depend on ``ImagePublisher`` rather than this class.
    """

    def __init__(
        self,
        host: str,
        timeout: int = 25,
        *,
        session: requests.Session | None = None,
        selection_delay: float = 0.20,
    ) -> None:
        if not host:
            raise ValueError("GeekMagic host cannot be empty.")

        self.base_url = (
            host.rstrip("/")
            if host.startswith(("http://", "https://"))
            else f"http://{host.rstrip('/')}"
        )
        self.timeout = (4, int(timeout))
        self.session = session or requests.Session()
        self.selection_delay = max(0.0, float(selection_delay))

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        response = self.session.get(
            self.base_url + path,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    def list_images(self) -> list[RemoteImage]:
        html = self._get(
            "/filelist",
            {"dir": "/image/"},
        ).text

        pattern = re.compile(
            r"<a href='(?P<path>[^']+)'>"
            r"(?P<name>[^<]+)"
            r"</a></td><td>"
            r"(?P<size>[^<]+)"
            r"</td>"
        )

        return [
            RemoteImage(**match.groupdict())
            for match in pattern.finditer(html)
        ]

    def upload_image(
        self,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        try:
            response = self.session.post(
                self.base_url + "/doUpload?dir=/image/",
                files={
                    "file": (
                        filename,
                        content,
                        mime_type,
                    )
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.RequestException as error:
            # Some firmware revisions close the connection after persisting
            # the upload. Verify device state before reporting a false failure.
            existing = {
                item.name
                for item in self.list_images()
            }
            if filename not in existing:
                raise RuntimeError(
                    f"Unable to upload {filename}: {error}"
                ) from error

    def delete_image(self, remote: RemoteImage) -> None:
        self._get("/delete", {"file": remote.path})

    def open_picture_app(self) -> None:
        """Open the stock Picture application."""

        response = self._get(
            "/set",
            {"open_app": "Picture"},
        )

        if response.text.strip().upper() == "FAIL":
            raise RuntimeError(
                "GeekMagic rejected the Picture application request."
            )

    def select_image(
        self,
        filename: str,
        *,
        autoplay: bool | None = None,
    ) -> None:
        """Select an album file through the stock firmware API.

        ``album_path`` selects the image. ``album_autoplay`` is omitted when
        ``autoplay`` is ``None`` so the existing autoplay state is preserved.
        """

        self.open_picture_app()

        if self.selection_delay:
            time.sleep(self.selection_delay)

        params: dict[str, Any] = {
            "album_path": f"/image/{filename}",
        }

        if autoplay is not None:
            params["album_autoplay"] = 1 if autoplay else 0

        response = self._get("/set", params)

        if response.text.strip().upper() == "FAIL":
            raise RuntimeError(
                f"GeekMagic rejected image selection for {filename}."
            )

    def configure_rotation(
        self,
        enabled: bool,
        interval: int,
    ) -> None:
        # Matches the stock web UX:
        # /set?gif_loop=1&i_i=<seconds>&autoplay=<0|1>
        response = self._get(
            "/set",
            {
                "gif_loop": 1,
                "i_i": max(1, int(interval)),
                "autoplay": 1 if enabled else 0,
            },
        )

        if response.text.strip().upper() == "FAIL":
            raise RuntimeError(
                "GeekMagic rejected the slideshow configuration."
            )
