from __future__ import annotations

import httpx
from mcp.server.fastmcp import FastMCP

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

mcp = FastMCP(
    name="live-weather-toolkit",
    instructions="Provides live weather data for a named city using Open-Meteo.",
)


async def _fetch_json(url: str, params: dict[str, object]) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_city_weather(city: str) -> dict[str, object]:
    """Fetch live weather for a city and return a structured snapshot."""

    geocode = await _fetch_json(
        GEOCODE_URL,
        {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        },
    )
    results = geocode.get("results") or []
    if not results:
        return {
            "status": "not_found",
            "city": city,
            "message": "No city match was found.",
        }

    place = results[0]
    forecast = await _fetch_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "timezone": "auto",
            "forecast_days": 1,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        },
    )

    current = forecast.get("current", {})
    daily = forecast.get("daily", {})

    return {
        "status": "ok",
        "city": place.get("name", city),
        "country": place.get("country"),
        "admin1": place.get("admin1"),
        "latitude": place.get("latitude"),
        "longitude": place.get("longitude"),
        "timezone": forecast.get("timezone"),
        "current_temperature_c": current.get("temperature_2m"),
        "current_humidity_pct": current.get("relative_humidity_2m"),
        "current_precipitation_mm": current.get("precipitation"),
        "current_wind_speed_kmh": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "today_max_c": (daily.get("temperature_2m_max") or [None])[0],
        "today_min_c": (daily.get("temperature_2m_min") or [None])[0],
        "today_precipitation_sum_mm": (daily.get("precipitation_sum") or [None])[0],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

