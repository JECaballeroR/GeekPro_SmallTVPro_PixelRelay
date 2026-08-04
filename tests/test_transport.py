from io import BytesIO

import pytest
from PIL import Image

from pixel_relay import (
    ImageNotFoundError,
    ImagePublisher,
    InvalidImageError,
    RemoteImage,
)


class FakeDisplay:
    def __init__(self):
        self.images: dict[str, bytes] = {}
        self.rotation = None

    def list_images(self) -> list[RemoteImage]:
        return [
            RemoteImage(
                name=name,
                path=f"/image/{name}",
                size=str(len(content)),
            )
            for name, content in self.images.items()
        ]

    def upload_image(self, filename, content, mime_type):
        self.images[filename] = content

    def delete_image(self, remote):
        self.images.pop(remote.name, None)

    def configure_rotation(self, enabled, interval):
        self.rotation = (enabled, interval)


def test_publish_bytes_is_independent_from_dashboard():
    display = FakeDisplay()
    publisher = ImagePublisher(display)

    result = publisher.publish_bytes("50_test.jpg", b"jpeg-data")

    assert result.name == "50_test.jpg"
    assert display.images["50_test.jpg"] == b"jpeg-data"


def test_publish_pillow_encodes_static_jpeg():
    display = FakeDisplay()
    publisher = ImagePublisher(display)
    source = Image.new("RGB", (240, 240), "black")

    publisher.publish_pillow("50_test.jpg", source)

    encoded = Image.open(BytesIO(display.images["50_test.jpg"]))
    assert encoded.format == "JPEG"
    assert encoded.size == (240, 240)


def test_reconcile_only_removes_managed_images_by_default():
    display = FakeDisplay()
    display.images = {
        "00_music.jpg": b"a",
        "10_fx.jpg": b"b",
        "family_photo.jpg": b"c",
    }
    publisher = ImagePublisher(
        display,
        managed_names={"00_music.jpg", "10_fx.jpg"},
    )

    deleted = publisher.reconcile({"00_music.jpg"})

    assert deleted == ["10_fx.jpg"]
    assert "family_photo.jpg" in display.images


def test_delete_missing_raises_clear_exception():
    publisher = ImagePublisher(FakeDisplay())

    with pytest.raises(ImageNotFoundError):
        publisher.delete("missing.jpg")


@pytest.mark.parametrize(
    "filename",
    ["", "../bad.jpg", "folder/bad.jpg", "image.txt"],
)
def test_invalid_remote_names_are_rejected(filename):
    publisher = ImagePublisher(FakeDisplay())

    with pytest.raises(InvalidImageError):
        publisher.publish_bytes(filename, b"x")
