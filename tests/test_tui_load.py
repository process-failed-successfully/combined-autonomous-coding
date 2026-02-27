import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from textual.app import App, ComposeResult
import asyncio
import sys

# Mock shared.load_lab and shared.charts before importing shared.tui_load
sys.modules['shared.load_lab'] = MagicMock()
sys.modules['shared.charts'] = MagicMock()

from shared.tui_load import LoadLabTab

class TestLoadLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create a test app to mount the widget
        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield LoadLabTab()

        self.app = TestApp()
        # Textual 0.40+ style testing
        # We don't process messages manually in setup for unit tests generally if we use run_test context

    async def test_compose(self):
        """Test that the widget composes correctly."""
        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(LoadLabTab)

            # Check for key widgets
            self.assertIsNotNone(tab.query_one("#load-url"))
            self.assertIsNotNone(tab.query_one("#load-method"))
            self.assertIsNotNone(tab.query_one("#load-users"))
            self.assertIsNotNone(tab.query_one("#load-duration"))
            self.assertIsNotNone(tab.query_one("#btn-run-load"))
            self.assertIsNotNone(tab.query_one("#load-stats-table"))
            self.assertIsNotNone(tab.query_one("#load-chart-log"))

    async def test_run_load_test(self):
        """Test the run load test flow."""
        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(LoadLabTab)

            # Mock the manager's run_load_test method
            # Note: We need to mock the coroutine return
            mock_results = {
                "total_requests": 100,
                "rps": 20.0,
                "success_count": 90,
                "error_count": 10,
                "latency": {
                    "min": 0.1, "avg": 0.2, "median": 0.15, "p95": 0.3, "p99": 0.4, "max": 0.5
                },
                "status_codes": {200: 90, 500: 10}
            }

            # Since _run_sync_wrapper calls asyncio.run(manager.run_load_test(...)),
            # we should mock manager.run_load_test to be an async function returning mock_results.

            async def mock_run(*args, **kwargs):
                return mock_results

            tab.manager.run_load_test = mock_run

            # Mock draw_ascii_bar_chart
            sys.modules['shared.charts'].draw_ascii_bar_chart.return_value = "Mock Chart"

            # Fill inputs
            tab.query_one("#load-url").value = "http://test.com"
            tab.query_one("#load-users").value = "5"
            tab.query_one("#load-duration").value = "2"

            # Click run
            # We mock _run_sync_wrapper directly because asyncio.run inside an async test loop causes issues
            tab._run_sync_wrapper = MagicMock(return_value=mock_results)

            await pilot.click("#btn-run-load")

            # Check table update
            table = tab.query_one("#load-stats-table")
            # Wait for update
            await pilot.pause()

            self.assertTrue(len(table.rows) > 0)

            # Check log update
            log = tab.query_one("#load-chart-log")

    async def test_validation(self):
        """Test validation when URL is empty."""
        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(LoadLabTab)

            # Mock notify
            tab.notify = MagicMock()

            # Empty URL
            tab.query_one("#load-url").value = ""

            await pilot.click("#btn-run-load")

            tab.notify.assert_called_with("URL required.", severity="error")

if __name__ == '__main__':
    unittest.main()
