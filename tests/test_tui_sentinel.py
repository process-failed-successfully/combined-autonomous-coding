import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, Checkbox, Switch, RichLog, Label
import pytest

from shared.tui_sentinel import SentinelTab

class SentinelApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield SentinelTab(self.project_dir)

class TestSentinelTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

        # Patch Sentinel class
        self.patcher = patch("shared.tui_sentinel.Sentinel")
        self.mock_sentinel_cls = self.patcher.start()
        self.mock_sentinel = self.mock_sentinel_cls.return_value

    def tearDown(self):
        self.patcher.stop()

    async def test_initial_state(self):
        app = SentinelApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(SentinelTab)

            # Check default config
            self.assertTrue(tab.query_one("#chk-lint", Checkbox).value)
            self.assertTrue(tab.query_one("#chk-test", Checkbox).value)
            self.assertFalse(tab.query_one("#chk-security", Checkbox).value)
            self.assertFalse(tab.query_one("#sw-autofix", Switch).value)

            # Check status
            self.assertIn("Stopped", str(tab.query_one("#lbl-sentinel-status", Label).render()))

    async def test_start_sentinel(self):
        app = SentinelApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(SentinelTab)

            # Click Start
            await pilot.click("#btn-sentinel-toggle")

            # Verify Sentinel initialized
            self.mock_sentinel_cls.assert_called_once()
            args, kwargs = self.mock_sentinel_cls.call_args
            self.assertEqual(args[0], self.project_dir)
            self.assertIn("lint", kwargs['checks'])

            # Verify Start called
            self.mock_sentinel.start.assert_called_once_with(blocking=False)

            # UI Updates
            btn = tab.query_one("#btn-sentinel-toggle", Button)
            self.assertEqual(str(btn.label), "Stop Sentinel")
            self.assertTrue(tab.query_one("#chk-lint").disabled)

    async def test_stop_sentinel(self):
        app = SentinelApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(SentinelTab)

            # Start
            await pilot.click("#btn-sentinel-toggle")

            # Stop
            await pilot.click("#btn-sentinel-toggle")

            # Verify Stop called
            self.mock_sentinel.stop.assert_called_once()

            # UI Updates
            btn = tab.query_one("#btn-sentinel-toggle", Button)
            self.assertEqual(str(btn.label), "Start Sentinel")
            self.assertFalse(tab.query_one("#chk-lint").disabled)

    async def test_log_callback(self):
        app = SentinelApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(SentinelTab)

            # Patch app.call_from_thread
            with patch.object(app, "call_from_thread") as mock_call:
                tab.log_message("Test Log")
                mock_call.assert_called()
                args = mock_call.call_args[0]
                self.assertEqual(args[1], "Test Log")

if __name__ == "__main__":
    unittest.main()
