import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import sys
import os

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.api_lab import ApiLabManager  # noqa: E402


class TestApiLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = ApiLabManager(self.project_dir)

    def test_load_spec_yaml(self):
        yaml_content = """
openapi: 3.0.0
servers:
  - url: http://api.example.com
paths:
  /users:
    get:
      summary: Get users
"""
        # We need to mock Path.exists to return True for openapi.yaml
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True
            with patch("builtins.open", mock_open(read_data=yaml_content)):
                success = self.manager.load_spec()
                self.assertTrue(success)

                endpoints = self.manager.list_endpoints()
                self.assertEqual(len(endpoints), 1)
                self.assertEqual(endpoints[0]['path'], '/users')
                self.assertEqual(endpoints[0]['method'], 'GET')

                url = self.manager.get_server_url()
                self.assertEqual(url, "http://api.example.com")

    @patch("requests.Session.request")
    def test_execute_request(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.text = '{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}
        mock_response.ok = True
        mock_request.return_value = mock_response

        result = self.manager.execute_request("GET", "http://test.com/api")

        self.assertEqual(result['status_code'], 200)
        self.assertTrue(result['success'])
        # JSON formatting adds indentation
        self.assertIn('"message": "success"', result['body'])

    def test_get_server_url_default(self):
        self.manager.spec_data = {}
        self.assertEqual(self.manager.get_server_url(), "http://localhost:8000")


if __name__ == "__main__":
    unittest.main()
