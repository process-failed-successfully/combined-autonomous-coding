import unittest
from unittest.mock import MagicMock
import json
import sys
import os

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.api_fuzzer import APIFuzzer  # noqa: E402
from shared.api_lab import ApiLabManager  # noqa: E402


class TestAPIFuzzer(unittest.TestCase):
    def setUp(self):
        self.mock_manager = MagicMock(spec=ApiLabManager)
        self.fuzzer = APIFuzzer(self.mock_manager)

    def test_fuzz_endpoint_parallel(self):
        # Setup mock execute_request
        def side_effect(method, url, body=None):
            payload = json.loads(body)
            # Simulate a crash for a specific payload
            if isinstance(payload, dict) and payload.get("crash"):
                return {'status_code': 500, 'success': False, 'body': 'Error'}
            return {'status_code': 200, 'success': True, 'body': 'OK'}

        self.mock_manager.execute_request.side_effect = side_effect

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }

        # We need to make sure we generate enough payloads to trigger parallelism
        # The default fuzzer generates quite a few for an object.

        results = self.fuzzer.fuzz_endpoint("POST", "http://test.com/api", schema)

        # Verify results
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # Check that execute_request was called
        self.assertTrue(self.mock_manager.execute_request.called)
        self.assertEqual(self.mock_manager.execute_request.call_count, len(results))

    def test_fuzz_endpoint_exceptions(self):
        # Test that exceptions in threads are handled
        self.mock_manager.execute_request.side_effect = Exception("Network Error")

        schema = {"type": "string"}
        results = self.fuzzer.fuzz_endpoint("POST", "http://test.com/api", schema)

        self.assertGreater(len(results), 0)
        for res in results:
            self.assertIn("error", res)
            self.assertEqual(res["error"], "Network Error")


if __name__ == "__main__":
    unittest.main()
