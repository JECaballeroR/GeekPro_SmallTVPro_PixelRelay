# Pixel Relay

**Pixel Relay by JECaballeroR** is a modular Python image relay and static
dashboard framework. It can send content to a GeekMagic SmallTV device while
keeping the stock firmware: **no ESPHome flashing is required**.

The long-term goal is to make small displays programmable through reusable
Python modules without replacing the firmware or coupling developers to the
full dashboard application.

## Features

- reusable, device-independent `ImagePublisher` API;
- GeekMagic SmallTV stock-firmware adapter;
- direct image sending without opening the GUI;
- static Windows music card;
- **Exchange Rate** card using USD/COP daily closes;
- Open-Meteo weather card;
- nearest strictly future timed Google Calendar event;
- minute-resolution clock;
- default thank-you notification card;
- GUI, headless, and Windows tray modes;
- `.env` configuration;
- pre-commit, tox, pytest, coverage, and GitHub Actions.

## Installation

```powershell
py -m pip install -e .
copy .env.example .env
```

Or run:

```text
scripts\install.bat
```

Interactive local configuration:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/configure_local.ps1
```

## Run modes

```powershell
# Full Tkinter interface
py -m pixel_relay gui

# No application window
py -m pixel_relay headless

# Windows system tray with quick actions
pyw -m pixel_relay tray
```

## Use only the image sender

The transport layer does not start Tkinter, WinRT, calendar services, or the
dashboard scheduler:

```python
from pixel_relay import GeekMagicDevice, ImagePublisher

publisher = ImagePublisher(
    GeekMagicDevice("192.168.1.63")
)
publisher.publish_file(
    "status.jpg",
    remote_name="50_status.jpg",
)
```

CLI equivalent:

```powershell
pixel-relay send status.jpg --name 50_status.jpg
```

See [`docs/transport.md`](docs/transport.md) and [`examples/`](examples/).

## Configuration

Copy `.env.example` to `.env`. The included calendar URL is explicitly fake
and exists only to demonstrate the expected Google Calendar ICS format.
Replace it with your own private URL before enabling the calendar module.

`.env`, local JSON configuration, logs, virtual environments, coverage files,
and build artifacts are ignored by Git.

Local GUI configuration:

```text
%APPDATA%\PixelRelay\config.json
```

Tray logs:

```text
%APPDATA%\PixelRelay\logs\pixel-relay.log
```

## Direct music selection

When Windows playback starts or the track identity changes, Pixel Relay waits
briefly for the updated JPEG to settle and sends only the album selection:

```text
/set?album_path=%2Fimage%2F00_music.jpg
```

Pixel Relay does **not** send `open_app=Picture`.

When **Pause autoplay while music is focused** is enabled, the same request also
contains `album_autoplay=0`. No immediate second pause request is sent.

After the configured focus duration, rotation resumes using:

```text
/set?gif_loop=1&i_i=<seconds>&autoplay=1
```

When pause-on-focus is disabled, Pixel Relay only changes `album_path` and
leaves the current autoplay state unchanged.

## If automatic rotation stops

Pixel Relay uses the device's stock Picture/Album behavior. If the display
stops rotating for any reason, open the GeekMagic **web UX** at the device IP
and enable **Auto Rotate / Autoplay** again. After that, restart or resume
rotation from Pixel Relay.

This recovery step is performed in the stock web interface; it does not
require flashing ESPHome.

## Project structure

```text
src/pixel_relay/
├── cli.py
├── config.py
├── constants.py
├── monitor.py
├── runtime.py
├── tray.py
├── ui.py
├── devices/
│   └── geekmagic.py
├── transport/
│   ├── errors.py
│   ├── models.py
│   ├── protocols.py
│   └── publisher.py
├── media/
│   └── windows.py
├── modules/
│   ├── music.py
│   ├── fx.py
│   ├── weather.py
│   ├── calendar.py
│   ├── clock.py
│   └── notifications.py
└── rendering/
    └── common.py
```

## Development workflow

```powershell
py -m pip install -e ".[dev]"
pre-commit install
pre-commit run --all-files
tox
```

## Reference implementation and attribution

The original device-communication approach was informed by
[`adrienbrault/geekmagic-hacs`](https://github.com/adrienbrault/geekmagic-hacs),
especially its documentation of stock GeekMagic HTTP endpoints, firmware
profiles, Picture album behavior, and server-side Pillow rendering.

That project is MIT licensed. See [`NOTICE.md`](NOTICE.md).

Pixel Relay is independent from Home Assistant, GeekMagic, and ESPHome.
