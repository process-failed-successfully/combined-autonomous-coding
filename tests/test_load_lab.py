import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import sys

# Ensure aiohttp is mocked if not present
sys.modules['aiohttp'] = MagicMock()

from shared.load_lab import LoadLabManager

class TestLoadLab(unittest.TestCase):
    def test_calculate_stats(self):
        manager = LoadLabManager()
        results = [
            {"latency": 0.1, "status": 200, "error": None},
            {"latency": 0.2, "status": 200, "error": None},
            {"latency": 0.5, "status": 500, "error": None},
            {"latency": 0.1, "status": 0, "error": "Connection Error"},
        ]
        total_duration = 1.0

        stats = manager._calculate_stats(results, total_duration)

        self.assertEqual(stats["total_requests"], 4)
        self.assertEqual(stats["rps"], 4.0)
        self.assertEqual(stats["success_count"], 3)
        self.assertEqual(stats["error_count"], 1)
        self.assertEqual(stats["status_codes"][200], 2)
        self.assertEqual(stats["status_codes"][500], 1)

        self.assertEqual(stats["latency"]["min"], 0.1)
        self.assertEqual(stats["latency"]["max"], 0.5)
        self.assertAlmostEqual(stats["latency"]["avg"], 0.225)

class TestLoadLabAsync(unittest.TestCase):
    def test_run_load_test_real_time(self):
        # Mock Response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read.return_value = b"ok"

        # Mock Request Context Manager
        mock_request_ctx = AsyncMock()
        mock_request_ctx.__aenter__.return_value = mock_response
        mock_request_ctx.__aexit__.return_value = None

        # Mock Session
        # session.request() is not async, it returns an async context manager.
        mock_session = MagicMock()
        mock_session.request.return_value = mock_request_ctx

        # Mock Session Context Manager
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None

        # Configure the global mock
        from shared.load_lab import aiohttp as mock_aiohttp_module
        # ClientSession() returns the context manager
        mock_aiohttp_module.ClientSession.return_value = mock_session_ctx

        manager = LoadLabManager()

        # Run for a short duration
        result = asyncio.run(manager.run_load_test("http://test.com", users=2, duration=0.1))

        self.assertGreater(result["total_requests"], 0)
        self.assertEqual(result["error_count"], 0)
        self.assertEqual(result["success_count"], result["total_requests"])

if __name__ == '__main__':
    unittest.main()
