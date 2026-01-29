import unittest
from unittest.mock import MagicMock
from shared.api_fuzzer import APIFuzzer

class TestAPIFuzzer(unittest.TestCase):
    def setUp(self):
        self.mock_manager = MagicMock()
        self.fuzzer = APIFuzzer(self.mock_manager)

    def test_generate_valid_payload_string(self):
        schema = {"type": "string"}
        val = self.fuzzer.generate_valid_payload(schema)
        self.assertIsInstance(val, str)

    def test_generate_valid_payload_object(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        val = self.fuzzer.generate_valid_payload(schema)
        self.assertIsInstance(val, dict)
        self.assertIsInstance(val.get("name"), str)
        self.assertIsInstance(val.get("age"), int)

    def test_generate_fuzz_payloads(self):
        base = {"name": "test", "age": 10}
        payloads = list(self.fuzzer.generate_fuzz_payloads(base))

        # Should contain base
        self.assertIn(base, payloads)

        # Should contain missing field
        self.assertTrue(any("name" not in p for p in payloads if isinstance(p, dict)))

        # Should contain type mismatch
        self.assertTrue(any(p.get("age") == "not_an_int" for p in payloads if isinstance(p, dict)))

    def test_fuzz_endpoint(self):
        # Setup mock execute_request
        self.mock_manager.execute_request.return_value = {
            "status_code": 200,
            "success": True
        }

        schema = {
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"id": {"type": "integer"}}
                        }
                    }
                }
            }
        }

        results = self.fuzzer.fuzz_endpoint("POST", "/test", schema)

        # Check that we got results
        self.assertGreater(len(results), 0)

        # Verify execute_request was called multiple times
        self.assertGreater(self.mock_manager.execute_request.call_count, 1)

if __name__ == '__main__':
    unittest.main()
