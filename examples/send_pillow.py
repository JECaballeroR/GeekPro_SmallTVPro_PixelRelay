"""Render and send a Pillow image through the public transport API."""

import os

from PIL import Image, ImageDraw

from pixel_relay import GeekMagicDevice, ImagePublisher


image = Image.new("RGB", (240, 240), "#000000")
draw = ImageDraw.Draw(image)
draw.text((120, 120), "Hello Pixel Relay", fill="#ffffff", anchor="mm")

publisher = ImagePublisher(
    GeekMagicDevice(
        os.getenv("PIXEL_DEVICE_IP", "192.168.1.63")
    )
)
publisher.publish_pillow("50_hello.jpg", image)
