import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio

from textual.app import App
from shared.tui_load import LoadLabTab

class DummyApp(App):
    def compose(self):
        yield LoadLabTab("/tmp")

class TestLoadLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_ui_and_worker(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(LoadLabTab)
            self.assertIsNotNone(tab)

            # Since the worker is a thread worker running an event loop internally now,
            # we need to mock it in a way that doesn't explode in the isolated loop.
            # But the easiest way is to mock run_load_test as an AsyncMock
            tab.manager.run_load_test = AsyncMock(return_value={
                "total_requests": 15, "duration": 2.5, "rps": 6.0, "success_count": 15, "error_count": 0,
                "latency": {"min": 0.1, "max": 0.5, "avg": 0.2, "p95": 0.4, "p99": 0.45}
            })

            tab.query_one("#url-input").value = "http://localhost:8080"
            tab.query_one("#users-input").value = "5"
            tab.query_one("#duration-input").value = "2"

            tab.query_one("#start-btn").press()

            # Wait for the worker to finish
            await pilot.pause(0.3)

            # Check if run_load_test was called with the correct args
            tab.manager.run_load_test.assert_called_once_with(
                url="http://localhost:8080",
                users=5,
                duration=2,
                method="GET"
            )

            table = tab.query_one("#results-table")
            self.assertGreater(table.row_count, 0)

            # Optional: Wait a bit more to ensure updates
            await pilot.pause(0.1)

if __name__ == "__main__":
    unittest.main()
