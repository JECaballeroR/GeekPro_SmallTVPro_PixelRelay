# Contributing

1. Create a virtual environment.
2. Install with `py -m pip install -e ".[dev]"`.
3. Run `pre-commit install`.
4. Keep vendor endpoints inside `devices/`.
5. Keep reusable publishing behavior inside `transport/`.
6. Keep data retrieval and rendering inside the corresponding module.
7. Add fake-device tests for transport changes.
8. Run `pre-commit run --all-files`, `tox` and `pytest`.

Never commit `.env`, private calendar URLs, device IPs from private networks
or personal event details.
