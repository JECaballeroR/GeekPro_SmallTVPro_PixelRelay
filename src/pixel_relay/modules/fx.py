"""USD/COP data retrieval and daily-close chart rendering."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from urllib.parse import quote

import requests
from PIL import ImageDraw

from ..constants import ACCENT, DIM, MUTED, WHITE
from ..rendering.common import (
    base_image,
    format_cop,
    image_to_jpeg,
    load_font,
    trim_text,
)

finance_http = requests.Session()
finance_http.headers["User-Agent"] = "Mozilla/5.0 Pixel-Relay/1.1"

def yahoo_range_for_days(history_days: int) -> str:
    if history_days <= 30:
        return "1mo"
    if history_days <= 90:
        return "3mo"
    if history_days <= 180:
        return "6mo"
    return "1y"

def fetch_fx_data(
    symbol: str,
    history_days: int = 30,
) -> dict[str, Any]:
    encoded = quote(symbol, safe="")
    last_error = None
    history_days = max(5, min(365, int(history_days)))

    for hostname in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            response = finance_http.get(
                f"https://{hostname}/v8/finance/chart/{encoded}",
                params={
                    "interval": "1d",
                    "range": yahoo_range_for_days(history_days),
                    "includePrePost": "false",
                    "events": "div,splits",
                },
                timeout=15,
            )
            response.raise_for_status()

            result = response.json()["chart"]["result"][0]
            metadata = result.get("meta", {})
            timestamps = result.get("timestamp") or []
            closes = (
                result.get("indicators", {})
                .get("quote", [{}])[0]
                .get("close", [])
            )

            daily_points = [
                (int(timestamp), float(close))
                for timestamp, close in zip(timestamps, closes)
                if close is not None
            ][-history_days:]

            current_price = metadata.get("regularMarketPrice")
            if current_price is None and daily_points:
                current_price = daily_points[-1][1]

            if current_price is None:
                raise RuntimeError("Yahoo did not return a current value.")

            previous_close = (
                metadata.get("chartPreviousClose")
                or metadata.get("previousClose")
            )

            if previous_close is None and len(daily_points) >= 2:
                previous_close = daily_points[-2][1]

            percent = None
            absolute_change = None

            if previous_close:
                absolute_change = float(current_price) - float(previous_close)
                percent = (
                    absolute_change
                    / float(previous_close)
                    * 100
                )

            market_time = int(
                metadata.get("regularMarketTime")
                or time.time()
            )

            current_day = (
                datetime.fromtimestamp(market_time)
                .astimezone()
                .date()
            )

            if daily_points:
                last_day = (
                    datetime.fromtimestamp(daily_points[-1][0])
                    .astimezone()
                    .date()
                )

                if last_day == current_day:
                    daily_points[-1] = (
                        market_time,
                        float(current_price),
                    )
                else:
                    daily_points.append(
                        (market_time, float(current_price))
                    )
            else:
                daily_points = [
                    (market_time, float(current_price))
                ]

            return {
                "symbol": symbol,
                "price": float(current_price),
                "previous_close": (
                    float(previous_close)
                    if previous_close is not None
                    else None
                ),
                "absolute_change": absolute_change,
                "percent": percent,
                "points": daily_points[-history_days:],
                "market_time": market_time,
                "history_days": history_days,
            }

        except Exception as error:
            last_error = error

    raise RuntimeError(f"Yahoo Finance: {last_error}")

def draw_daily_close_chart(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, float]],
    previous_close: float | None,
    box: tuple[int, int, int, int],
):
    x1, y1, x2, y2 = box
    values = [value for _, value in points]

    if len(values) < 2:
        draw.text(
            (x1, (y1 + y2) // 2),
            "Not enough daily closes yet",
            font=load_font(9),
            fill=DIM,
            anchor="lm",
        )
        return

    reference_values = list(values)
    if previous_close is not None:
        reference_values.append(previous_close)

    minimum = min(reference_values)
    maximum = max(reference_values)
    spread = maximum - minimum or 1.0
    padding = spread * 0.10
    minimum -= padding
    maximum += padding
    spread = maximum - minimum or 1.0

    line_color = (
        "#4fd18b"
        if values[-1] >= values[0]
        else "#ff6b6b"
    )

    def value_to_y(value: float) -> int:
        normalized = (value - minimum) / spread
        return round(y2 - normalized * (y2 - y1))

    if previous_close is not None:
        reference_y = value_to_y(previous_close)
        for start_x in range(x1, x2, 8):
            draw.line(
                (
                    start_x,
                    reference_y,
                    min(start_x + 4, x2),
                    reference_y,
                ),
                fill="#535353",
                width=1,
            )

    coordinates = []
    count = len(values)

    for index, value in enumerate(values):
        x = x1 + (x2 - x1) * index / max(1, count - 1)
        coordinates.append((round(x), value_to_y(value)))

    draw.line(
        coordinates,
        fill=line_color,
        width=2,
        joint="curve",
    )

    for x, y in coordinates:
        draw.ellipse(
            (x - 2, y - 2, x + 2, y + 2),
            fill=line_color,
        )

    last_x, last_y = coordinates[-1]
    draw.ellipse(
        (last_x - 4, last_y - 4, last_x + 4, last_y + 4),
        outline=WHITE,
        width=1,
    )

def create_fx_slide(
    fx_data: dict[str, Any] | None,
    config: dict[str, Any],
    error: str | None = None,
) -> bytes:
    scale = float(config["font_scale"])
    image, draw = base_image(ACCENT)

    header_font = load_font(13, True, scale)
    rate_font = load_font(30, True, scale)
    label_font = load_font(10, True, scale)
    detail_font = load_font(11, True, scale)
    close_font = load_font(10, False, scale)
    footer_font = load_font(9, False, scale)

    draw.text(
        (31, 31),
        "EXCHANGE RATE",
        font=header_font,
        fill=ACCENT,
    )

    if fx_data:
        draw.text(
            (31, 70),
            format_cop(fx_data["price"]),
            font=rate_font,
            fill=WHITE,
            anchor="lm",
        )
        draw.text(
            (31, 98),
            "USD → COP · CURRENT RATE",
            font=label_font,
            fill=MUTED,
            anchor="lm",
        )

        previous_close = fx_data.get("previous_close")

        if previous_close is not None:
            draw.text(
                (31, 119),
                f"Previous close: {format_cop(previous_close)}",
                font=close_font,
                fill=DIM,
                anchor="lm",
            )

        if fx_data["percent"] is not None:
            change_color = (
                "#4fd18b"
                if fx_data["percent"] >= 0
                else "#ff6b6b"
            )
            draw.text(
                (208, 119),
                f"{fx_data['percent']:+.3f}%",
                font=detail_font,
                fill=change_color,
                anchor="rm",
            )

        if bool(config["show_fx_plot"]):
            draw_daily_close_chart(
                draw,
                fx_data["points"],
                previous_close,
                (31, 140, 208, 190),
            )

        updated = (
            datetime.fromtimestamp(fx_data["market_time"])
            .astimezone()
            .strftime("%d %b · %H:%M")
        )

        draw.text(
            (31, 210),
            f"YAHOO · {fx_data['history_days']} DAILY CLOSES",
            font=footer_font,
            fill=DIM,
            anchor="lm",
        )
        draw.text(
            (208, 210),
            updated.upper(),
            font=footer_font,
            fill=MUTED,
            anchor="rm",
        )

    else:
        draw.text(
            (31, 89),
            "NOT AVAILABLE",
            font=load_font(23, True, scale),
            fill="#f0ba57",
            anchor="lm",
        )
        draw.text(
            (31, 133),
            trim_text(
                draw,
                error or "Could not query Yahoo",
                load_font(10, False, scale),
                177,
            ),
            font=load_font(10, False, scale),
            fill=DIM,
            anchor="lm",
        )

    return image_to_jpeg(image)
