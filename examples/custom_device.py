"""Skeleton adapter for adding another display implementation."""

from pixel_relay import ImagePublisher, RemoteImage


class MyDisplay:
    def list_images(self) -> list[RemoteImage]:
        return []

    def upload_image(
        self,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        # Call the vendor API here.
        ...

    def delete_image(self, remote: RemoteImage) -> None:
        ...

    def configure_rotation(
        self,
        enabled: bool,
        interval: int,
    ) -> None:
        ...


publisher = ImagePublisher(MyDisplay())
publisher.publish_file("dashboard.jpg")
