import calendar
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Any
from shared.task_manager import TaskManager, Task

class CalendarLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.task_manager = TaskManager(project_dir)
        self.tasks_cache: List[Task] = []
        self.cal = calendar.Calendar(firstweekday=0) # Monday is 0

    def refresh_tasks(self) -> None:
        """Refreshes the task cache."""
        self.tasks_cache = self.task_manager.fetch_all_tasks()

    def get_month_matrix(self, year: int, month: int) -> List[List[Optional[int]]]:
        """
        Returns a matrix representing the month's calendar.
        Each row is a week, containing day numbers (int) or None.
        """
        # monthcalendar returns 0 for days outside the month
        matrix = self.cal.monthdayscalendar(year, month)
        # Convert 0 to None for clearer API
        return [[d if d != 0 else None for d in week] for week in matrix]

    def get_events_for_month(self, year: int, month: int) -> Dict[int, List[Task]]:
        """
        Returns a dictionary mapping day numbers to lists of tasks for that day.
        Events are mapped by due_date. If no due_date, they are not shown on calendar
        (or maybe shown on created_at? For now, let's stick to due_date).
        """
        if not self.tasks_cache:
            self.refresh_tasks()

        events: Dict[int, List[Task]] = {}

        for task in self.tasks_cache:
            # Check due date
            if task.due_date and task.due_date.year == year and task.due_date.month == month:
                day = task.due_date.day
                if day not in events:
                    events[day] = []
                events[day].append(task)

            # Optionally check created_at for start?
            # For simplicity, we just map due_date for now as "deadlines"

        return events

    def render_ascii_calendar(self, year: int, month: int) -> str:
        """Renders a text-based calendar with task counts."""
        events = self.get_events_for_month(year, month)
        matrix = self.get_month_matrix(year, month)

        month_name = calendar.month_name[month]
        output = [f"{month_name} {year}".center(28)]
        output.append("Mo Tu We Th Fr Sa Su")

        for week in matrix:
            line = ""
            for day in week:
                if day is None:
                    line += "   " # 3 spaces
                else:
                    # Check if there are events
                    count = len(events.get(day, []))
                    if count > 0:
                        # Highlight days with events (e.g. *12)
                        day_str = f"*{day:<2}" if day < 10 else f"*{day}"
                        # Ensure it fits in 2 chars + space?
                        # Standard format is 2 chars right aligned.
                        # Let's use brackets for events: [1]
                        # Or just bold/color in TUI.
                        # For ASCII, maybe just: 12*
                        day_str = f"{day:>2}*"
                    else:
                        day_str = f"{day:>2} "
                    line += day_str
            output.append(line)

        return "\n".join(output)

    def get_tasks_for_date(self, target_date: date) -> List[Task]:
        """Returns tasks due on a specific date."""
        if not self.tasks_cache:
            self.refresh_tasks()

        matches = []
        for task in self.tasks_cache:
            if task.due_date and task.due_date.date() == target_date:
                matches.append(task)
        return matches
