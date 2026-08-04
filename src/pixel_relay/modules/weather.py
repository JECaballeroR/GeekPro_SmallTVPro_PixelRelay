"""Open-Meteo weather data and weather slide rendering."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import requests

from ..constants import ACCENT, DIM, MUTED, TRACK, WHITE
from ..rendering.common import (
    base_image,
    image_to_jpeg,
    load_font,
    trim_text,
)

weather_http = requests.Session()
weather_http.headers["User-Agent"] = "Pixel-Relay/1.1"

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Heavy thunderstorm with hail",
}


def geocode_weather_location(city: str, country_code: str) -> dict[str, Any]:
    response = weather_http.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 10,
            "language": "es",
            "format": "json",
            "countryCode": country_code.upper(),
        },
        timeout=15,
    )
    response.raise_for_status()

    results = response.json().get("results") or []
    if not results:
        raise RuntimeError(
            f"Could not find {city}, {country_code} in the weather service."
        )

    # Prefer an exact city and country match.
    normalized_city = city.strip().casefold()
    normalized_country = country_code.strip().upper()

    selected = next(
        (
            item
            for item in results
            if str(item.get("name", "")).casefold() == normalized_city
            and str(item.get("country_code", "")).upper() == normalized_country
        ),
        results[0],
    )

    return {
        "name": selected.get("name") or city,
        "country_code": selected.get("country_code") or country_code,
        "latitude": float(selected["latitude"]),
        "longitude": float(selected["longitude"]),
        "timezone": selected.get("timezone") or "America/Bogota",
    }

def fetch_weather_no_key(city: str, country_code: str) -> dict[str, Any]:
    location = geocode_weather_location(city, country_code)

    response = weather_http.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timezone": "auto",
            "current": ",".join(
                [
                    "temperature_2m",
                    "apparent_temperature",
                    "relative_humidity_2m",
                    "weather_code",
                    "wind_speed_10m",
                    "cloud_cover",
                    "surface_pressure",
                    "is_day",
                ]
            ),
            "wind_speed_unit": "kmh",
            "forecast_days": 1,
        },
        timeout=15,
    )
    response.raise_for_status()

    payload = response.json()
    current = payload.get("current") or {}

    required = (
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "weather_code",
        "wind_speed_10m",
    )

    missing = [key for key in required if current.get(key) is None]
    if missing:
        raise RuntimeError(
            "The weather service did not return: " + ", ".join(missing)
        )

    code_value = int(current["weather_code"])

    return {
        "city": str(location["name"]),
        "country": str(location["country_code"]),
        "description": WMO_WEATHER_CODES.get(
            code_value,
            f"Weather code {code_value}",
        ),
        "temperature": float(current["temperature_2m"]),
        "feels_like": float(current["apparent_temperature"]),
        "humidity": int(round(float(current["relative_humidity_2m"]))),
        "wind": float(current["wind_speed_10m"]),
        "clouds": int(round(float(current.get("cloud_cover") or 0))),
        "pressure": (
            int(round(float(current["surface_pressure"])))
            if current.get("surface_pressure") is not None
            else None
        ),
        "is_day": bool(current.get("is_day", 1)),
        "timestamp": int(time.time()),
    }

def create_weather_slide(
    weather: dict[str, Any] | None,
    config: dict[str, Any],
    error: str | None = None,
) -> bytes:
    scale = float(config["font_scale"])
    image, draw = base_image("#4ad7d1")

    header_font = load_font(14, True, scale)
    temp_font = load_font(45, True, scale)
    description_font = load_font(16, True, scale)
    metric_font = load_font(12, True, scale)
    footer_font = load_font(10, False, scale)

    if weather:
        place = " · ".join(
            part
            for part in (weather["city"], weather["country"])
            if part
        ).upper()

        draw.text(
            (29, 28),
            trim_text(draw, place, header_font, 192),
            font=header_font,
            fill="#4ad7d1",
        )

        draw.text(
            (121, 82),
            f"{weather['temperature']:.0f}°",
            font=temp_font,
            fill=WHITE,
            anchor="mm",
        )

        draw.text(
            (121, 119),
            trim_text(
                draw,
                weather["description"],
                description_font,
                190,
            ),
            font=description_font,
            fill=MUTED,
            anchor="mm",
        )

        draw.line((28, 143, 212, 143), fill=TRACK, width=2)

        draw.text(
            (30, 162),
            f"Feels {weather['feels_like']:.0f}°",
            font=metric_font,
            fill=WHITE,
        )
        draw.text(
            (30, 184),
            f"Humidity {weather['humidity']}%",
            font=metric_font,
            fill=MUTED,
        )
        draw.text(
            (138, 162),
            f"Wind {weather['wind']:.0f} km/h",
            font=metric_font,
            fill=WHITE,
        )
        draw.text(
            (138, 184),
            f"Clouds {weather['clouds']}%",
            font=metric_font,
            fill=MUTED,
        )

        updated = (
            datetime.fromtimestamp(weather["timestamp"])
            .astimezone()
            .strftime("%H:%M")
        )

        draw.text(
            (29, 218),
            "OPEN-METEO",
            font=footer_font,
            fill=DIM,
            anchor="lm",
        )
        draw.text(
            (211, 218),
            updated,
            font=footer_font,
            fill=MUTED,
            anchor="rm",
        )

    else:
        draw.text(
            (29, 28),
            f"WEATHER · {str(config['weather_city']).upper()}",
            font=header_font,
            fill="#4ad7d1",
        )
        draw.text(
            (121, 101),
            "NOT AVAILABLE",
            font=load_font(23, True, scale),
            fill="#f0ba57",
            anchor="mm",
        )
        draw.text(
            (121, 148),
            trim_text(
                draw,
                error or "Could not retrieve weather",
                load_font(11, False, scale),
                184,
            ),
            font=load_font(11, False, scale),
            fill=MUTED,
            anchor="mm",
        )

    return image_to_jpeg(image)
