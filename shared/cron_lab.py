import datetime
from typing import List
from croniter import croniter

class CronLabManager:
    """Manages cron expression operations."""

    def validate(self, expression: str) -> bool:
        """Checks if a cron expression is valid."""
        return croniter.is_valid(expression)

    def explain(self, expression: str) -> str:
        """Returns a human-readable explanation."""
        if not self.validate(expression):
            return "Invalid cron expression."

        # Ideally we would use a library like cron-descriptor here.
        # For now, we confirm validity.
        return "Valid cron expression."

    def next_occurrences(self, expression: str, count: int = 5) -> List[str]:
        """Returns the next N occurrences."""
        if not self.validate(expression):
            return []

        base = datetime.datetime.now()
        cron_iter = croniter(expression, base)
        results = []
        for _ in range(count):
            results.append(str(cron_iter.get_next(datetime.datetime)))
        return results
