import unittest
from unittest.mock import MagicMock
from pathlib import Path
from shared.api_lab import ApiLabManager

class TestLoadTesterBackend(unittest.TestCase):
    def test_load_test_endpoint(self):
        # Mock project dir
        manager = ApiLabManager(Path("."))

        # Mock session to avoid real network calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True

        # We need to mock manager.session.request
        manager.session.request = MagicMock(return_value=mock_response)

        # Run load test
        print("Running load test...")
        results = manager.load_test_endpoint("GET", "http://test.local", users=2, duration=1)

        print("Results:", results)

        # Verify structure
        self.assertIn("total_requests", results)
        self.assertIn("rps", results)
        self.assertIn("avg_latency", results)
        self.assertIn("errors", results)
        self.assertIn("status_codes", results)

        # Verify values (approximate since it depends on execution speed)
        self.assertGreater(results["total_requests"], 0)
        self.assertEqual(results["errors"], 0)
        self.assertEqual(results["status_codes"].get(200), results["total_requests"])

if __name__ == "__main__":
    unittest.main()
