import unittest
import time
from unittest.mock import MagicMock
import sys
import os

# Ensure shared module is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.api_load_tester import APILoadTester  # noqa: E402


class TestAPILoadTester(unittest.TestCase):
    def setUp(self):
        self.mock_manager = MagicMock()
        self.tester = APILoadTester(self.mock_manager)

    def test_run_load_test(self):
        # Mock session.request
        mock_response = MagicMock()
        mock_response.status_code = 200

        # Add a small delay to simulate network latency
        # We use a very small delay to ensure the test runs quickly but still exercises threads
        def side_effect(*args, **kwargs):
            time.sleep(0.01)  # 10ms
            return mock_response

        self.mock_manager.session.request.side_effect = side_effect

        # Run for 0.5 second with 2 users (fast test)
        results = self.tester.run_load_test("GET", "http://test.com", users=2, duration=0.5)

        self.assertIn("total_requests", results)
        self.assertIn("rps", results)
        self.assertIn("avg_latency", results)

        self.assertGreater(results["total_requests"], 0)
        self.assertGreater(results["rps"], 0)
        self.assertEqual(results["errors"], 0)
        self.assertEqual(results["status_codes"].get(200), results["total_requests"])

    def test_run_load_test_with_errors(self):
        # Mock 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500

        self.mock_manager.session.request.return_value = mock_response

        results = self.tester.run_load_test("GET", "http://test.com", users=2, duration=0.5)

        self.assertGreater(results["total_requests"], 0)
        self.assertEqual(results["errors"], results["total_requests"])
        self.assertEqual(results["status_codes"].get(500), results["total_requests"])


if __name__ == '__main__':
    unittest.main()
