import httpx
from typing import Any
from ..config import settings


class WeatherTool:
    name = "get_weather"
    description = "Get current weather for a location using Open-Meteo (no API key)."
    input_schema = {"location": "city or 'lat,lon'"}

    async def run(self, **kwargs) -> str:
        location = kwargs.get("location")
        if not location:
            return "Please provide a location."

        # If user passes "lat,lon", use it; otherwise geocode via Open-Meteo Nominatim
        lat = lon = None
        if "," in location and all(part.strip().replace(".", "", 1).replace("-", "").isdigit() for part in location.split(",", 1)):
            lat, lon = [p.strip() for p in location.split(",", 1)]
        else:
            async with httpx.AsyncClient(timeout=10) as client:
                gresp = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search", params={"name": location, "count": 1}
                )
                gresp.raise_for_status()
                gdata = gresp.json()
                if not gdata.get("results"):
                    return f"Couldn't geocode '{location}'."
                lat = gdata["results"][0]["latitude"]
                lon = gdata["results"][0]["longitude"]

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                settings.WEATHER_API_BASE,
                params={"latitude": lat, "longitude": lon, "current_weather": True},
            )
            resp.raise_for_status()
            data = resp.json()
        cw = data.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        return f"Current weather at {location}: {temp}°C, wind {wind} km/h."