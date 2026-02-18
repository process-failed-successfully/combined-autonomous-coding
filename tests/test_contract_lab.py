import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.contract_lab import ContractVerifier

class TestContractVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = ContractVerifier()

    def test_generate_valid_payload(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        payload = self.verifier.generate_valid_payload(schema)
        self.assertIn("name", payload)
        self.assertNotIn("age", payload) # Only required by default in my implementation
        self.assertEqual(payload["name"], "string")

    @patch("requests.Session.request")
    def test_verify_endpoint_success(self, mock_request):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Test"}
        mock_request.return_value = mock_response

        operation = {
            "responses": {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"}
                                },
                                "required": ["id"]
                            }
                        }
                    }
                }
            }
        }

        result = self.verifier.verify_endpoint("GET", "http://test.com/api", operation)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["status_code"], 200)

    @patch("requests.Session.request")
    def test_verify_endpoint_fail_schema(self, mock_request):
        # Mock bad response (missing id)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "Test"}
        mock_request.return_value = mock_response

        operation = {
            "responses": {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"}
                                },
                                "required": ["id"]
                            }
                        }
                    }
                }
            }
        }

        result = self.verifier.verify_endpoint("GET", "http://test.com/api", operation)
        self.assertEqual(result["status"], "fail")
        self.assertIn("Schema Validation Failed", result["errors"][0])

    @patch("requests.Session.request")
    def test_verify_endpoint_undocumented_status(self, mock_request):
        # Mock undocumented status
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_request.return_value = mock_response

        operation = {
            "responses": {
                "200": {}
            }
        }

        result = self.verifier.verify_endpoint("POST", "http://test.com/api", operation)
        self.assertEqual(result["status"], "fail")
        self.assertIn("Undocumented status code", result["errors"][0])

if __name__ == '__main__':
    unittest.main()
