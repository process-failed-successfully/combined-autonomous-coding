import sys
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
import calendar
import json

class DateLabManager:
    """Manages Date Lab operations: addition, subtraction, diff, info, format."""

    def _parse_date(self, date_str: str) -> datetime:
        """Parses a date string (ISO 8601 or YYYY-MM-DD)."""
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            # Fallback for some simple formats
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    pass
            raise ValueError(f"Could not parse date '{date_str}'")

    def add_date(self, date_str: str, days: int = 0, weeks: int = 0) -> str:
        """Adds days/weeks to a date."""
        try:
            dt = self._parse_date(date_str)
            result = dt + timedelta(days=days, weeks=weeks)
            return result.isoformat()
        except ValueError as e:
            return f"Error: {e}"

    def sub_date(self, date_str: str, days: int = 0, weeks: int = 0) -> str:
        """Subtracts days/weeks from a date."""
        try:
            dt = self._parse_date(date_str)
            result = dt - timedelta(days=days, weeks=weeks)
            return result.isoformat()
        except ValueError as e:
            return f"Error: {e}"

    def diff_dates(self, date1_str: str, date2_str: str) -> Dict[str, Any]:
        """Calculates difference between two dates."""
        try:
            dt1 = self._parse_date(date1_str)
            dt2 = self._parse_date(date2_str)

            diff = dt2 - dt1

            # Count business days
            # Simple approximation: iterate over days
            business_days = 0
            curr = dt1 if dt1 < dt2 else dt2
            end = dt2 if dt1 < dt2 else dt1
            while curr < end:
                if curr.weekday() < 5:  # Monday-Friday are 0-4
                    business_days += 1
                curr += timedelta(days=1)

            if dt1 > dt2:
                business_days = -business_days

            return {
                "success": True,
                "days": diff.days,
                "seconds": diff.seconds,
                "total_seconds": diff.total_seconds(),
                "business_days": business_days
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def get_info(self, date_str: str) -> Dict[str, Any]:
        """Gets info about a date (weekday, weekend, leap year, etc)."""
        try:
            dt = self._parse_date(date_str)
            year = dt.year
            month = dt.month

            return {
                "success": True,
                "year": year,
                "month": month,
                "day": dt.day,
                "weekday": calendar.day_name[dt.weekday()],
                "is_weekend": dt.weekday() >= 5,
                "is_leap_year": calendar.isleap(year),
                "days_in_month": calendar.monthrange(year, month)[1],
                "day_of_year": dt.timetuple().tm_yday,
                "iso_calendar": dt.isocalendar() # year, week, weekday
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def format_date(self, date_str: str, fmt: str) -> str:
        """Formats a date to a specific string format."""
        try:
            dt = self._parse_date(date_str)
            return dt.strftime(fmt)
        except ValueError as e:
            return f"Error: {e}"

def run_date_lab_logic(args) -> bool:
    """CLI handler for Date Lab."""
    manager = DateLabManager()

    if args.action == "add":
        print(manager.add_date(args.date, days=args.days, weeks=args.weeks))
        return True

    elif args.action == "sub":
        print(manager.sub_date(args.date, days=args.days, weeks=args.weeks))
        return True

    elif args.action == "diff":
        result = manager.diff_dates(args.date1, args.date2)
        if result["success"]:
            print(f"Days: {result['days']}")
            print(f"Business Days: {result['business_days']}")
            print(f"Total Seconds: {result['total_seconds']}")
        else:
            print(result["error"], file=sys.stderr)
            return False
        return True

    elif args.action == "info":
        result = manager.get_info(args.date)
        if result["success"]:
            print(json.dumps(result, indent=2))
        else:
            print(result["error"], file=sys.stderr)
            return False
        return True

    elif args.action == "format":
        print(manager.format_date(args.date, args.format))
        return True

    return False
