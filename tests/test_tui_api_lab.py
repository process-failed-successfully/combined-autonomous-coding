import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
import asyncio
from shared.tui import ApiLabTab

class TestTuiApiLab(unittest.IsolatedAsyncioTestCase):
    async def test_run_load_test(self):
        # Mock the project directory
        project_dir = Path("/tmp/test_project")

        # Instantiate the tab
        tab = ApiLabTab(project_dir)

        # Mock the manager
        tab.manager = MagicMock()
        # Mock load_test_endpoint to be a regular function (since run_load_test uses asyncio.to_thread)
        tab.manager.load_test_endpoint = MagicMock(return_value={
            "total_requests": 100,
            "rps": 50.0,
            "avg_latency": 10.0,
            "p50_latency": 5.0,
            "p95_latency": 15.0,
            "p99_latency": 20.0,
            "errors": 0,
            "status_codes": {200: 100}
        })

        # Mock query_one to return mock widgets
        mock_widgets = {
            "#api-load-method": MagicMock(value="GET"),
            "#api-load-url": MagicMock(value="http://test.local"),
            "#api-load-users": MagicMock(value="5"),
            "#api-load-duration": MagicMock(value="2"),
            "#api-load-body": MagicMock(text='{"key": "value"}'),
            "#api-load-log": MagicMock(),
            "#btn-api-load-start": MagicMock()
        }

        def side_effect(selector, type=None):
            if selector in mock_widgets:
                return mock_widgets[selector]
            raise Exception(f"Widget not found: {selector}")

        tab.query_one = MagicMock(side_effect=side_effect)

        # Mock notify (method of App/Widget)
        tab.notify = MagicMock()

        # Run the method
        await tab.run_load_test()

        # Verify manager called correctly
        tab.manager.load_test_endpoint.assert_called_once_with(
            "GET", "http://test.local", 5, 2, '{"key": "value"}'
        )

        # Verify log was written to
        log = mock_widgets["#api-load-log"]
        self.assertTrue(log.write.called)
        # Check for success message
        args, _ = log.write.call_args_list[-1]
        # We can't strictly check the exact last call, but we can check if write was called with metrics
        calls = [c[0][0] for c in log.write.call_args_list]
        self.assertTrue(any("Test Complete" in str(c) for c in calls))
        self.assertTrue(any("Total Requests: 100" in str(c) for c in calls))

if __name__ == "__main__":
    unittest.main()
