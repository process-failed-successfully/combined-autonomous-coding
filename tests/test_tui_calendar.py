import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_calendar import CalendarTab
from textual.app import App

class TestCalendarTab(unittest.TestCase):
    def setUp(self):
        self.mock_project_dir = Path("/tmp/mock_project")

    @patch("shared.tui_calendar.CalendarLabManager")
    def test_navigation_logic(self, mock_manager_class):
        # We can test the logic methods without mounting the widget in an App
        # However, Textual widgets rely on self.query_one which fails if not mounted.
        # So we can't easily call update_calendar directly.
        # But we can test change_month logic if we mock update_calendar.

        tab = CalendarTab(self.mock_project_dir)
        tab.update_calendar = MagicMock()

        # Test Next Month
        tab.current_year = 2023
        tab.current_month = 10

        tab.change_month(1)
        self.assertEqual(tab.current_month, 11)
        self.assertEqual(tab.current_year, 2023)

        # Test Year Rollover (Dec -> Jan)
        tab.current_month = 12
        tab.change_month(1)
        self.assertEqual(tab.current_month, 1)
        self.assertEqual(tab.current_year, 2024)

        # Test Year Rollover (Jan -> Dec)
        tab.change_month(-1)
        self.assertEqual(tab.current_month, 12)
        self.assertEqual(tab.current_year, 2023)

if __name__ == '__main__':
    unittest.main()
