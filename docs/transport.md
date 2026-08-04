# Image transport API

`ImagePublisher` is the stable integration surface for developers. It does
not import Tkinter, WinRT, calendar code, or dashboard modules.

The purpose of this layer is to send content to supported devices while
keeping their stock firmware. A developer can use the relay API without
flashing ESPHome.

## Send bytes

```python
from pixel_relay import GeekMagicDevice, ImagePublisher

publisher = ImagePublisher(GeekMagicDevice("192.168.1.63"))
publisher.publish_bytes("50_status.jpg", jpeg_bytes)
```

## Send a file

```python
publisher.publish_file(
    "build/status.jpg",
    remote_name="50_status.jpg",
)
```

## Send a Pillow image

```python
from PIL import Image

image = Image.new("RGB", (240, 240), "black")
publisher.publish_pillow("50_status.jpg", image)
```

## Add another device

Implement the `ImageDisplay` protocol:

- `list_images()`;
- `upload_image()`;
- `delete_image()`;
- `select_image()`;
- `configure_rotation()`.

`ImagePublisher` can then use the adapter without changes.

## Rotation troubleshooting

If a GeekMagic display stops rotating, open its stock web UX and re-enable
**Auto Rotate / Autoplay**. Pixel Relay can then resume the album rotation.


## Select an image immediately

```python
publisher.select_image(
    "00_music.jpg",
    autoplay=False,
)
```

For GeekMagic, this sends `album_path=/image/00_music.jpg` without
switching the device application. Passing `autoplay=False` also sends
`album_autoplay=0`; omitting it preserves the existing autoplay state.

The slideshow interval is controlled separately:

```python
publisher.set_rotation(
    enabled=True,
    interval=5,
)
```

The GeekMagic adapter maps this to `gif_loop=1`, `i_i=5`, and `autoplay=1`.
