import unittest
import sys
import os
import json

sys.path.append(os.getcwd())

from shared.date_lab import DateLabManager

class TestDateLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = DateLabManager()

    def test_add_date_days(self):
        result = self.manager.add_date("2023-01-01", days=5)
        self.assertEqual(result, "2023-01-06T00:00:00")

    def test_add_date_weeks(self):
        result = self.manager.add_date("2023-01-01", weeks=2)
        self.assertEqual(result, "2023-01-15T00:00:00")

    def test_sub_date(self):
        result = self.manager.sub_date("2023-01-15", days=5)
        self.assertEqual(result, "2023-01-10T00:00:00")

    def test_diff_dates(self):
        result = self.manager.diff_dates("2023-01-01", "2023-01-10")
        self.assertTrue(result["success"])
        self.assertEqual(result["days"], 9)
        self.assertEqual(result["business_days"], 6) # Mon-Fri count

    def test_diff_dates_reverse(self):
        result = self.manager.diff_dates("2023-01-10", "2023-01-01")
        self.assertTrue(result["success"])
        self.assertEqual(result["days"], -9)
        self.assertEqual(result["business_days"], -6)

    def test_get_info(self):
        result = self.manager.get_info("2024-02-29") # Leap year
        self.assertTrue(result["success"])
        self.assertEqual(result["year"], 2024)
        self.assertEqual(result["month"], 2)
        self.assertEqual(result["day"], 29)
        self.assertTrue(result["is_leap_year"])
        self.assertEqual(result["weekday"], "Thursday")
        self.assertFalse(result["is_weekend"])

    def test_get_info_weekend(self):
        result = self.manager.get_info("2023-10-28") # Saturday
        self.assertTrue(result["success"])
        self.assertTrue(result["is_weekend"])

    def test_format_date(self):
        result = self.manager.format_date("2023-10-25", "%Y/%m/%d")
        self.assertEqual(result, "2023/10/25")

    def test_parse_error(self):
        result = self.manager.get_info("invalid-date")
        self.assertFalse(result["success"])
        self.assertIn("Could not parse date", result["error"])


# Adding textual TUI tests
import pytest
import asyncio
try:
    import textual
    from textual.app import App
    from textual.widgets import TabbedContent
    from shared.tui_date import DateLabTab
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


if TEXTUAL_AVAILABLE:
    class DateLabTestApp(App):
        def compose(self):
            with TabbedContent():
                yield DateLabTab()


@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual not installed")
@pytest.mark.asyncio
async def test_date_lab_tab_render():
    app = DateLabTestApp()
    async with app.run_test() as pilot:
        # Check basic rendering without interactions
        tab = app.query_one(DateLabTab)
        assert tab is not None

if __name__ == '__main__':
    unittest.main()
