"""
Weather Lab
===========

Utilities for fetching weather data using OpenMeteo API.
"""

import sys
import requests
from typing import Dict, Any, Optional
from shared.geo_lab import GeoLabManager

class WeatherLabManager:
    """Manages weather data fetching."""

    def __init__(self):
        self.geo_manager = GeoLabManager()
        self.api_url = "https://api.open-meteo.com/v1/forecast"

    def get_weather(self, query: str, units: str = "metric") -> Dict[str, Any]:
        """
        Fetches current weather and forecast for a location.
        """
        # Resolve location
        location = self.geo_manager.locate(query)
        if location.get("status") == "fail":
            return {"error": f"Location not found: {location.get('message')}"}

        lat = location.get("lat")
        lon = location.get("lon")

        if lat is None or lon is None:
             return {"error": "Could not determine coordinates."}

        # Prepare API request
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "timezone": location.get("timezone", "auto")
        }

        if units == "imperial":
            params["temperature_unit"] = "fahrenheit"
            params["windspeed_unit"] = "mph"
            params["precipitation_unit"] = "inch"

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Enrich with location info
            data["location"] = {
                "city": location.get("city"),
                "region": location.get("regionName"),
                "country": location.get("country")
            }
            return data
        except Exception as e:
            return {"error": str(e)}

    def get_weather_code_description(self, code: int) -> str:
        """Returns description for WMO weather code."""
        # Simplified WMO codes
        codes = {
            0: "Clear sky",
            1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Fog", 48: "Depositing rime fog",
            51: "Drizzle: Light", 53: "Drizzle: Moderate", 55: "Drizzle: Dense",
            61: "Rain: Slight", 63: "Rain: Moderate", 65: "Rain: Heavy",
            71: "Snow fall: Slight", 73: "Snow fall: Moderate", 75: "Snow fall: Heavy",
            77: "Snow grains",
            80: "Rain showers: Slight", 81: "Rain showers: Moderate", 82: "Rain showers: Violent",
            85: "Snow showers: Slight", 86: "Snow showers: Heavy",
            95: "Thunderstorm: Slight or moderate",
            96: "Thunderstorm with hail: Slight", 99: "Thunderstorm with hail: Heavy"
        }
        return codes.get(code, "Unknown")

def run_weather_lab_logic(args):
    """CLI handler for Weather Lab."""
    manager = WeatherLabManager()

    if not args.city:
        # Default to IP-based location if not provided
        args.city = "" # GeoLabManager handles empty query as IP lookup

    print(f"--- Weather for: {args.city or 'Current Location'} ---")

    data = manager.get_weather(args.city, units=args.units)

    if "error" in data:
        print(f"❌ Error: {data['error']}", file=sys.stderr)
        sys.exit(1)

    loc = data.get("location", {})
    curr = data.get("current_weather", {})
    daily = data.get("daily", {})

    print(f"Location: {loc.get('city')}, {loc.get('region')}, {loc.get('country')}")

    # Current
    temp = curr.get("temperature")
    wind = curr.get("windspeed")
    code = curr.get("weathercode")
    desc = manager.get_weather_code_description(code)

    unit_symbol = "°F" if args.units == "imperial" else "°C"
    wind_unit = "mph" if args.units == "imperial" else "km/h"

    print(f"\n[Current]")
    print(f"Condition: {desc}")
    print(f"Temp:      {temp}{unit_symbol}")
    print(f"Wind:      {wind} {wind_unit}")

    # Forecast
    if args.action == "forecast" and daily:
        print(f"\n[Forecast]")
        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        codes = daily.get("weathercode", [])

        for i, date in enumerate(times[:3]): # Show 3 days
            d_desc = manager.get_weather_code_description(codes[i])
            print(f"{date}: {min_temps[i]} - {max_temps[i]}{unit_symbol} ({d_desc})")

    sys.exit(0)
