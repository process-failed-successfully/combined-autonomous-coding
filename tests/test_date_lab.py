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

    def test_to_epoch(self):
        # 2023-01-01T00:00:00Z -> 1672531200
        result = self.manager.to_epoch("2023-01-01T00:00:00+00:00")
        self.assertEqual(result, "1672531200")

    def test_to_epoch_invalid(self):
        result = self.manager.to_epoch("invalid")
        self.assertTrue(result.startswith("Error"))

    def test_from_epoch(self):
        # 1672531200 -> 2023-01-01T00:00:00
        # datetime.fromtimestamp uses local time by default, but we can verify isoformat
        result = self.manager.from_epoch("1672531200")
        # Since it uses local timezone, we just check that it's a valid isoformat string
        # and has 2022/2023 depending on TZ
        self.assertIn("T", result)
        self.assertTrue(result.startswith("202"))

    def test_from_epoch_invalid(self):
        result = self.manager.from_epoch("invalid")
        self.assertTrue(result.startswith("Error"))


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

if __name__ == '__main__':
    unittest.main()

from shared.date_lab import run_date_lab_logic

class DummyArgs:
    def __init__(self, action, date=None, epoch=None, format=None):
        self.action = action
        self.date = date
        self.epoch = epoch
        self.format = format

class TestRunDateLabLogic(unittest.TestCase):
    def test_run_date_lab_logic_to_epoch_success(self):
        args = DummyArgs("to-epoch", date="2023-01-01T00:00:00+00:00")
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_to_epoch_fail(self):
        args = DummyArgs("to-epoch", date="invalid")
        self.assertFalse(run_date_lab_logic(args))

    def test_run_date_lab_logic_from_epoch_success(self):
        args = DummyArgs("from-epoch", epoch="1672531200")
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_from_epoch_fail(self):
        args = DummyArgs("from-epoch", epoch="invalid")
        self.assertFalse(run_date_lab_logic(args))

    def test_run_date_lab_logic_add(self):
        args = DummyArgs("add", date="2023-01-01")
        args.days = 5
        args.weeks = 0
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_sub(self):
        args = DummyArgs("sub", date="2023-01-01")
        args.days = 5
        args.weeks = 0
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_diff(self):
        args = DummyArgs("diff")
        args.date1 = "2023-01-01"
        args.date2 = "2023-01-10"
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_info(self):
        args = DummyArgs("info", date="2023-01-01")
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_format(self):
        args = DummyArgs("format", date="2023-01-01", format="%Y")
        self.assertTrue(run_date_lab_logic(args))

    def test_run_date_lab_logic_invalid_action(self):
        args = DummyArgs("unknown")
        self.assertFalse(run_date_lab_logic(args))


import pytest

try:
    from shared.tui_date import DateLabTab
    from textual.app import App
    from textual.widgets import Input, Button
    from textual.widgets import RichLog
except ImportError:
    pass

@pytest.mark.asyncio
async def test_date_lab_tui_to_epoch(monkeypatch):
    if not TEXTUAL_AVAILABLE:
        return

    class DateLabTestApp(App):
        def compose(self):
            yield DateLabTab()

    app = DateLabTestApp()
    async with app.run_test(size=(100, 100)) as pilot:
        tab = app.query_one(DateLabTab)

        # Select epoch tab if needed (Textual tabs might need switching, but we can query inputs directly)
        date_input = tab.query_one("#epoch-date-input", Input)
        date_input.value = "2023-01-01"

        to_epoch_btn = tab.query_one("#btn-to-epoch", Button)
        tab.do_to_epoch()

        log_widget = tab.query_one("#epoch-result", RichLog)
        content = ""
        for line in log_widget.lines:
            content += line.text + "\n"
        print("CONTENT IS:", content)

        # test from-epoch
        timestamp_input = tab.query_one("#epoch-timestamp-input", Input)
        timestamp_input.value = "1672531200"

        from_epoch_btn = tab.query_one("#btn-from-epoch", Button)
        tab.do_from_epoch()

        content = ""
        for line in log_widget.lines:
            content += line.text + "\n"
        print("CONTENT IS:", content)

        # test errors
        date_input.value = "invalid"
        tab.do_to_epoch()
        content = ""
        for line in log_widget.lines:
            content += line.text + "\n"
        print("CONTENT IS:", content)

        timestamp_input.value = "invalid"
        tab.do_from_epoch()
        content = ""
        for line in log_widget.lines:
            content += line.text + "\n"
        print("CONTENT IS:", content)

        # Empty tests
        date_input.value = ""
        tab.do_to_epoch()

        timestamp_input.value = ""
        tab.do_from_epoch()
