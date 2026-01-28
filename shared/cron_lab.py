from croniter import croniter
from datetime import datetime
from typing import List

class CronLabManager:
    """Manages cron expression parsing and calculation."""

    def validate(self, expression: str) -> bool:
        """Validates a cron expression."""
        return croniter.is_valid(expression)

    def get_next_occurrences(self, expression: str, count: int = 5) -> List[str]:
        """Calculates the next N occurrences."""
        if not self.validate(expression):
            return []

        base = datetime.now()
        iter = croniter(expression, base)
        results = []
        for _ in range(count):
            results.append(str(iter.get_next(datetime)))
        return results

    def describe(self, expression: str) -> str:
        """Provides a basic description of the cron expression."""
        if not self.validate(expression):
            return "Invalid expression."

        # Simple preset matching
        presets = {
            "* * * * *": "Every minute",
            "*/5 * * * *": "Every 5 minutes",
            "0 * * * *": "Every hour",
            "0 0 * * *": "Every day at midnight",
            "0 0 * * 0": "Every Sunday at midnight",
            "0 0 1 * *": "First day of every month at midnight",
            "@hourly": "Every hour",
            "@daily": "Every day at midnight",
            "@weekly": "Every week",
            "@monthly": "Every month",
            "@yearly": "Every year",
            "@annually": "Every year"
        }

        if expression in presets:
            return presets[expression]

        # Basic analysis
        parts = expression.split()
        if len(parts) >= 5:
            minute, hour, dom, month, dow = parts[:5]

            if minute == "*" and hour == "*" and dom == "*" and month == "*" and dow == "*":
                return "Every minute"

            if "/" in minute:
                return f"Every {minute.split('/')[1]} minutes"

            if minute != "*" and hour == "*":
                return f"Every hour at minute {minute}"

            if minute != "*" and hour != "*" and dom == "*" and month == "*" and dow == "*":
                return f"Every day at {hour}:{minute}"

        return "Custom schedule"
