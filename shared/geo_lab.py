import sys
import math
import requests
from typing import Dict, Any


class GeoLabManager:
    """Manages geolocation utilities."""

    def __init__(self):
        self.api_url = "http://ip-api.com/json/"

    def locate(self, query: str) -> Dict[str, Any]:
        """
        Locates an IP address or domain name.
        """
        try:
            url = f"{self.api_url}{query}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "fail", "message": str(e)}

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, float]:
        """
        Calculates the Haversine distance between two points.
        """
        R = 6371  # Earth radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance_km = R * c
        distance_miles = distance_km * 0.621371

        return {
            "km": round(distance_km, 2),
            "miles": round(distance_miles, 2)
        }

    def map_url(self, lat: float, lon: float) -> str:
        """
        Generates a Google Maps URL for the coordinates.
        """
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"


def run_geo_lab_logic(args):
    """CLI entry point for Geo Lab."""
    manager = GeoLabManager()

    if args.action == "locate":
        query = args.query
        print(f"--- Locating: {query} ---")
        result = manager.locate(query)
        if result.get("status") == "success":
            lat = result.get('lat', 0.0)
            lon = result.get('lon', 0.0)
            print(f"IP: {result.get('query')}")
            print(f"Location: {result.get('city')}, {result.get('regionName')}, {result.get('country')}")
            print(f"Coordinates: {lat}, {lon}")
            print(f"ISP: {result.get('isp')}")
            print(f"Timezone: {result.get('timezone')}")
            print(f"Map: {manager.map_url(float(lat), float(lon))}")
        else:
            print(f"❌ Failed: {result.get('message')}")
            sys.exit(1)

    elif args.action == "distance":
        try:
            # Parse inputs. Expecting "lat1,lon1" "lat2,lon2"
            p1 = args.point1.split(',')
            p2 = args.point2.split(',')
            lat1, lon1 = float(p1[0]), float(p1[1])
            lat2, lon2 = float(p2[0]), float(p2[1])

            dist = manager.calculate_distance(lat1, lon1, lat2, lon2)
            print("--- Distance ---")
            print(f"From: {lat1}, {lon1}")
            print(f"To:   {lat2}, {lon2}")
            print(f"Result: {dist['km']} km ({dist['miles']} miles)")
        except (ValueError, IndexError):
            print("❌ Error: Coordinates must be in 'lat,lon' format (e.g., 40.7128,-74.0060).", file=sys.stderr)
            sys.exit(1)

    elif args.action == "map":
        try:
            p = args.point.split(',')
            lat, lon = float(p[0]), float(p[1])
            print("--- Map Link ---")
            print(manager.map_url(lat, lon))
        except (ValueError, IndexError):
            print("❌ Error: Coordinates must be in 'lat,lon' format.", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
