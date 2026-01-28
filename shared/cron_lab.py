from datetime import datetime
from typing import List, Optional
from croniter import croniter

class CronLabManager:
    """Manages cron expression parsing and calculation."""

    @staticmethod
    def validate(expression: str) -> bool:
        """Validates a cron expression."""
        return croniter.is_valid(expression)

    @staticmethod
    def get_next_runs(expression: str, count: int = 5, start_time: Optional[datetime] = None) -> List[datetime]:
        """Calculates the next N occurrences."""
        if not CronLabManager.validate(expression):
            raise ValueError("Invalid cron expression")

        if start_time is None:
            start_time = datetime.now()

        # croniter requires a datetime object with valid tzinfo or naive (system local)
        # We use system local time by default if not provided
        iter = croniter(expression, start_time)
        results = []
        for _ in range(count):
            results.append(iter.get_next(datetime))
        return results

    @staticmethod
    def describe(expression: str) -> str:
        """Generates a human-readable description."""
        if not CronLabManager.validate(expression):
            return "Invalid expression"

        parts = expression.split()
        if len(parts) < 5:
             return "Invalid format (needs at least 5 fields)"

        # Normalize
        minute, hour, dom, month, dow = parts[:5]

        # Simple heuristic description
        if minute == "*" and hour == "*" and dom == "*" and month == "*" and dow == "*":
            return "Every minute"

        desc = []

        # Minute
        if minute == "*":
            desc.append("Every minute")
        elif minute.startswith("*/"):
            desc.append(f"Every {minute[2:]} minutes")
        else:
            desc.append(f"At minute {minute}")

        # Hour
        if hour == "*":
            if minute != "*" and not minute.startswith("*/"):
                desc.append("of every hour")
        elif hour.startswith("*/"):
             desc.append(f"past every {hour[2:]} hours")
        else:
             desc.append(f"past hour {hour}")

        # Day constraints
        constraints = []
        if dom != "*":
            constraints.append(f"on day-of-month {dom}")
        if month != "*":
            constraints.append(f"in month {month}")
        if dow != "*":
            constraints.append(f"on day-of-week {dow}")

        if constraints:
            desc.append(", " + ", ".join(constraints))

        return " ".join(desc)
