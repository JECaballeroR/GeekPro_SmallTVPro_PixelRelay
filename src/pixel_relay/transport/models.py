"""Value objects used by image transports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RemoteImage:
    """An image already stored on a display device."""

    name: str
    path: str
    size: str | None = None
