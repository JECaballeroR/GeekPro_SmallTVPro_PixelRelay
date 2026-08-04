"""Send one image without running the Pixel Relay dashboard."""

import os

from pixel_relay import GeekMagicDevice, ImagePublisher


device = GeekMagicDevice(
    os.getenv("PIXEL_DEVICE_IP", "192.168.1.63")
)
publisher = ImagePublisher(device)

publisher.publish_file(
    "example.jpg",
    remote_name="50_example.jpg",
)
