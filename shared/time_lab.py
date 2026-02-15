import sys
from datetime import datetime, timezone
import zoneinfo
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional

class TimeLabManager:
    """Manages Time Lab operations: current time, conversion, diff, epoch, and zones."""

    def get_current_time(self, tz_name: str = "UTC") -> str:
        """Returns the current time in the specified timezone."""
        try:
            tz = ZoneInfo(tz_name)
            now = datetime.now(tz)
            return now.isoformat()
        except zoneinfo.ZoneInfoNotFoundError:
            return f"Error: Timezone '{tz_name}' not found."

    def convert_time(self, value: str, to_zone: str) -> str:
        """Converts a time string (ISO or timestamp) to a target timezone."""
        try:
            target_tz = ZoneInfo(to_zone)

            # Try parsing as timestamp (float or int)
            try:
                ts = float(value)
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            except ValueError:
                # Try parsing as ISO format
                dt = datetime.fromisoformat(value)
                if dt.tzinfo is None:
                    # Assume UTC if no timezone provided
                    dt = dt.replace(tzinfo=timezone.utc)

            converted = dt.astimezone(target_tz)
            return converted.isoformat()
        except zoneinfo.ZoneInfoNotFoundError:
            return f"Error: Timezone '{to_zone}' not found."
        except ValueError:
            return f"Error: Could not parse time '{value}'."

    def diff_time(self, time1: str, time2: str) -> str:
        """Calculates the difference between two times."""
        try:
            # Helper to parse time
            def parse(t):
                try:
                    ts = float(t)
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                except ValueError:
                    dt = datetime.fromisoformat(t)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt

            dt1 = parse(time1)
            dt2 = parse(time2)

            diff = dt2 - dt1
            return str(diff)
        except ValueError:
            return "Error: Could not parse input times."

    def get_epoch(self, time_str: Optional[str] = None) -> str:
        """Returns the Unix timestamp for a given time (or now)."""
        if not time_str:
            return str(datetime.now(timezone.utc).timestamp())

        try:
            dt = datetime.fromisoformat(time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return str(dt.timestamp())
        except ValueError:
            return f"Error: Could not parse time '{time_str}'."

    def list_zones(self, search_term: Optional[str] = None) -> List[str]:
        """Lists available timezones, optionally filtered."""
        zones = sorted(list(zoneinfo.available_timezones()))
        if search_term:
            search_term = search_term.lower()
            zones = [z for z in zones if search_term in z.lower()]
        return zones

    def get_common_timezones(self) -> List[str]:
        """Returns a list of commonly used timezones."""
        common_zones = [
            "UTC",
            "America/Los_Angeles", # US/Pacific
            "America/Denver",      # US/Mountain
            "America/Chicago",     # US/Central
            "America/New_York",    # US/Eastern
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Kolkata",
            "Australia/Sydney",
            "Pacific/Auckland"
        ]
        # Filter only available zones to be safe
        available = zoneinfo.available_timezones()
        return [z for z in common_zones if z in available]

def run_time_lab_logic(args) -> bool:
    """CLI handler for Time Lab."""
    manager = TimeLabManager()

    if args.action == "now":
        tz = args.timezone or "UTC"
        print(f"Current time in {tz}:")
        print(manager.get_current_time(tz))

    elif args.action == "convert":
        if not args.time or not args.to_zone:
            print("Error: --time and --to-zone are required.", file=sys.stderr)
            return False
        print(f"Converted time in {args.to_zone}:")
        print(manager.convert_time(args.time, args.to_zone))

    elif args.action == "diff":
        if not args.time1 or not args.time2:
            print("Error: --time1 and --time2 are required.", file=sys.stderr)
            return False
        print("Time difference:")
        print(manager.diff_time(args.time1, args.time2))

    elif args.action == "epoch":
        # args.time is optional
        print("Epoch timestamp:")
        print(manager.get_epoch(args.time))

    elif args.action == "zones":
        print("Available Timezones:")
        zones = manager.list_zones(args.search)
        if not zones:
            print("No timezones found.")
        else:
            # Print in columns if possible, but simple list for now
            for zone in zones:
                print(f"  {zone}")
            print(f"\nTotal: {len(zones)}")

    return True
