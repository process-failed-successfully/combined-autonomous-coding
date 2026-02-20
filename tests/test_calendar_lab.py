import unittest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch
from datetime import datetime
from shared.calendar_lab import CalendarLabManager
from shared.task_manager import Task

class TestCalendarLab(unittest.TestCase):
    def setUp(self):
        self.mock_project_dir = Path("/tmp/mock_project")
        # Patch TaskManager at class level or during setup to avoid instantiation issues
        self.task_manager_patcher = patch("shared.calendar_lab.TaskManager")
        self.mock_task_manager_class = self.task_manager_patcher.start()
        self.mock_tm = self.mock_task_manager_class.return_value

        self.manager = CalendarLabManager(self.mock_project_dir)

    def tearDown(self):
        self.task_manager_patcher.stop()

    def test_get_month_matrix(self):
        # Test Oct 2023
        # Oct 1st 2023 was a Sunday.
        matrix = self.manager.get_month_matrix(2023, 10)
        # First week: [25, 26, 27, 28, 29, 30, 1] if displaying previous month?
        # calendar.monthdayscalendar returns 0 for days outside month.
        # shared/calendar_lab.py converts 0 to None.

        # In Oct 2023:
        # Week 1 (starting Monday): 25..30 (Sep) -> None, 1 (Oct) -> 1
        # So [None, None, None, None, None, None, 1]
        self.assertEqual(matrix[0], [None, None, None, None, None, None, 1])

    def test_get_events_for_month(self):
        # Create dummy tasks
        t1 = Task(id="1", source="todo", title="Task 1", status="open", due_date=datetime(2023, 10, 5))
        t2 = Task(id="2", source="todo", title="Task 2", status="open", due_date=datetime(2023, 10, 5))
        t3 = Task(id="3", source="todo", title="Task 3", status="open", due_date=datetime(2023, 10, 10))
        t4 = Task(id="4", source="todo", title="Task 4", status="open", due_date=datetime(2023, 11, 1)) # Diff month

        self.mock_tm.fetch_all_tasks.return_value = [t1, t2, t3, t4]

        events = self.manager.get_events_for_month(2023, 10)

        self.assertIn(5, events)
        self.assertEqual(len(events[5]), 2)
        self.assertIn(10, events)
        self.assertEqual(len(events[10]), 1)
        self.assertNotIn(1, events) # Nov 1st shouldn't be in Oct events

    def test_render_ascii_calendar(self):
        t1 = Task(id="1", source="todo", title="Task 1", status="open", due_date=datetime(2023, 10, 1))
        self.mock_tm.fetch_all_tasks.return_value = [t1]

        output = self.manager.render_ascii_calendar(2023, 10)
        self.assertIn("October 2023", output)
        # Should contain "*1" or "1*" depending on implementation
        # Implementation: f"{day:>2}*" if events
        self.assertIn(" 1*", output)

if __name__ == '__main__':
    unittest.main()
