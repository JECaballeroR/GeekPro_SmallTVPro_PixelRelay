# Changelog

## 1.3.1 — 2026-08-04

- Removed `open_app=Picture` from music selection.
- Added a short configurable post-upload selection delay.
- Removed the duplicate pause request that could produce a black frame.
- Added music focus when playback starts, not only when the track changes.
- Resume requests continue to use `i_i` and `autoplay=1`.

## 1.3.0 — 2026-08-04

- Replaced album rebuilds with direct `album_path` image selection.
- Added optional `album_autoplay=0` music focus behavior.
- Added stock slideshow control using `gif_loop`, `i_i`, and `autoplay`.
- Added `ImagePublisher.select_image()` to the public transport API.
- Added firmware-request tests for direct selection and autoplay interval.
- Added a UX control for pausing autoplay while music is focused.

## 1.2.0 — 2026-08-04

- Corrected the previous product-name misspelling to Pixel Relay.
- Renamed the repository, package, CLI, environment variables, and code classes.
- Updated full branding to Pixel Relay by JECaballeroR.
- Kept JECR for compact marks and the default notification footer.
- Translated the application, generated cards, scripts, logs, and documentation to English.
- Changed the default weather example to Rovaniemi, Finland.
- Added a clearly fake Google Calendar ICS URL to `.env.example`.
- Renamed the USD/COP card to Exchange Rate.
- Added stock web UX autoplay recovery guidance.
- Documented the no-ESPHome, stock-firmware development goal.

## 1.1.0 — 2026-08-04

- Added the public device-independent `ImagePublisher` API.
- Added direct CLI image sending, tests, pre-commit, tox, and CI.
