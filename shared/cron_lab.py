import datetime
from typing import List
from croniter import croniter

class CronLabManager:
    """Manages cron expression validation and explanation."""

    def validate(self, expression: str) -> bool:
        """Checks if the cron expression is valid."""
        return croniter.is_valid(expression)

    def get_next_occurrences(self, expression: str, count: int = 5, start_time: datetime.datetime = None) -> List[datetime.datetime]:
        """Returns the next N occurrences of the schedule."""
        if not self.validate(expression):
            return []

        now = start_time if start_time else datetime.datetime.now()
        try:
            cron_itr = croniter(expression, now)
            results = []
            for _ in range(count):
                results.append(cron_itr.get_next(datetime.datetime))
            return results
        except Exception:
            return []

    def describe(self, expression: str) -> str:
        """Generates a simple human-readable description (heuristic)."""
        if not self.validate(expression):
            return "Invalid cron expression."

        parts = expression.split()
        if len(parts) < 5:
             return "Invalid format (too few fields)."

        # Basic heuristic - not comprehensive but helpful
        minute, hour, dom, month, dow = parts[:5]

        desc = []

        # Minute
        if minute == "*":
            desc.append("Every minute")
        elif "*/" in minute:
            desc.append(f"Every {minute.split('/')[1]} minutes")
        elif "," in minute:
            desc.append(f"At minutes {minute}")
        else:
            desc.append(f"At minute {minute}")

        # Hour
        if hour == "*":
            pass # Implied every hour unless specified otherwise
        elif "*/" in hour:
            desc.append(f"past every {hour.split('/')[1]} hours")
        elif "," in hour:
             desc.append(f"past hours {hour}")
        else:
            desc.append(f"past hour {hour}")

        # DOM
        if dom != "*":
            desc.append(f"on day-of-month {dom}")

        # Month
        if month != "*":
            desc.append(f"in month {month}")

        # DOW
        if dow != "*":
            desc.append(f"on day-of-week {dow}")

        return " ".join(desc)
