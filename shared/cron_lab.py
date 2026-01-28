from typing import List, Optional, Dict
from datetime import datetime
from croniter import croniter

class CronLabManager:
    """Manages Cron Lab operations (validation, explanation, generation)."""

    def __init__(self, project_dir=None):
        self.project_dir = project_dir

    def validate(self, expression: str) -> bool:
        """Checks if a cron expression is valid."""
        return croniter.is_valid(expression)

    def get_next_runs(self, expression: str, count: int = 5) -> List[datetime]:
        """Returns the next N run times for a valid expression."""
        if not self.validate(expression):
            return []

        base = datetime.now()
        iter = croniter(expression, base)
        return [iter.get_next(datetime) for _ in range(count)]

    def explain(self, expression: str) -> str:
        """Returns a human-readable explanation (heuristic)."""
        if not self.validate(expression):
            return "Invalid cron expression."

        # A simple heuristic explanation
        parts = expression.split()
        if len(parts) < 5:
            return "Invalid format (needs at least 5 fields)"

        minute, hour, dom, month, dow = parts[:5]

        desc = []
        if minute == "*" and hour == "*":
            desc.append("Every minute")
        elif minute != "*" and hour == "*":
            desc.append(f"At minute {minute} of every hour")
        elif minute == "0" and hour != "*":
            desc.append(f"At {hour}:00")
        else:
            desc.append(f"At {hour}:{minute}")

        if dom != "*" and month != "*":
            desc.append(f"on day {dom} of month {month}")
        elif dom != "*":
            desc.append(f"on day {dom} of every month")
        elif month != "*":
            desc.append(f"in month {month}")

        if dow != "*":
            desc.append(f"on day-of-week {dow}")

        return " ".join(desc)

    def generate_from_text(self, description: str) -> str:
        """Generates a cron expression from natural language (heuristic)."""
        description = description.lower()

        if "every minute" in description:
            return "* * * * *"
        if "hourly" in description or "every hour" in description:
            return "0 * * * *"
        if "daily" in description or "every day" in description:
            return "0 0 * * *"
        if "weekly" in description or "every week" in description:
            return "0 0 * * 0"
        if "monthly" in description or "every month" in description:
            return "0 0 1 * *"
        if "yearly" in description or "every year" in description:
            return "0 0 1 1 *"

        return "" # heuristic limit reached
