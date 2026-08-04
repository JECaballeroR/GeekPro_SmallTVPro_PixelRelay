# Architecture

## Product direction

**Pixel Relay by JECaballeroR** is designed to send generated content to small
displays without replacing stock firmware or flashing ESPHome.

## Layers

1. `modules/` retrieves data and creates static images.
2. `rendering/` provides shared Pillow primitives.
3. `transport/` validates and publishes images through a generic protocol.
4. `devices/` translates vendor APIs into the transport protocol.
5. `monitor.py` schedules updates and controls album state.
6. `ui.py`, `tray.py`, and `cli.py` are independent frontends.

## Dependency direction

```text
UI / tray / CLI
      ↓
   monitor
      ↓
ImagePublisher
      ↓
ImageDisplay protocol
      ↓
GeekMagicDevice
```

Modules never call device endpoints. Device adapters never know about music,
weather, calendar, exchange-rate, or notification semantics.

## Stock firmware recovery

The project relies on the device's stock Picture/Album mode. If automatic
rotation stops, open the device web UX and re-enable **Auto Rotate / Autoplay**.
This is a stock-firmware setting and does not require ESPHome.

## Quality gates

- `pre-commit` catches repository hygiene problems before commits.
- `tox` runs the same test contract across supported Python versions.
- GitHub Actions runs pre-commit and a Windows Python matrix.
- transport tests use a fake device and require no hardware.
