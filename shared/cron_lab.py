from croniter import croniter
from datetime import datetime
from typing import List, Optional

class CronLabManager:
    def validate(self, expression: str) -> bool:
        """Validates a cron expression."""
        return croniter.is_valid(expression)

    def get_next_occurrences(self, expression: str, count: int = 5, start_time: Optional[datetime] = None) -> List[datetime]:
        """Returns the next N occurrences of the cron expression."""
        if not self.validate(expression):
            return []

        if start_time is None:
            start_time = datetime.now()

        iter = croniter(expression, start_time)
        occurrences = []
        for _ in range(count):
            occurrences.append(iter.get_next(datetime))

        return occurrences

    def describe(self, expression: str) -> str:
        """Provides a human-readable description of the cron expression."""
        if not self.validate(expression):
            return "Invalid cron expression"

        # Simple manual description logic or use a library if available.
        # Since we don't want to add too many deps, we'll do a basic breakdown.
        parts = expression.split()
        if len(parts) != 5:
            return "Expression must have 5 parts (minute hour day-of-month month day-of-week)"

        minute, hour, dom, month, dow = parts

        desc = []

        # Time part
        if minute == "*" and hour == "*":
            desc.append("Every minute")
        elif minute != "*" and hour == "*":
            if "/" in minute:
                desc.append(f"Every {minute.split('/')[1]} minutes")
            else:
                desc.append(f"At minute {minute} of every hour")
        elif minute == "*" and hour != "*":
             if "/" in hour:
                 desc.append(f"Every minute past every {hour.split('/')[1]}th hour")
             else:
                 desc.append(f"Every minute of hour {hour}")
        else:
            # Specific time
            hour_str = hour.zfill(2) if hour.isdigit() else hour
            desc.append(f"At {hour_str}:{minute.zfill(2) if minute.isdigit() else minute}")

        # Date part
        date_desc = []
        if dom != "*":
            date_desc.append(f"on day-of-month {dom}")
        if month != "*":
            date_desc.append(f"in month {month}")
        if dow != "*":
            date_desc.append(f"on day-of-week {dow}")

        if date_desc:
            desc.append(" ".join(date_desc))
        else:
            desc.append("every day")

        return " ".join(desc)
