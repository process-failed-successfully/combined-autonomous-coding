import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os
from pathlib import Path
import json

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.api_lab import run_api_lab_cli, ApiLabManager

class TestApiLabCLI(unittest.TestCase):
    def setUp(self):
        self.mock_args = MagicMock()
        self.mock_args.project_dir = MagicMock()
        self.mock_args.project_dir.resolve.return_value = Path("/tmp/test_project")

    @patch("shared.api_lab.ApiLabManager")
    @patch("sys.exit")
    def test_list_command(self, mock_exit, MockManager):
        # Configure sys.exit to stop execution
        mock_exit.side_effect = SystemExit

        # Setup mock manager
        manager_instance = MockManager.return_value
        manager_instance.load_spec.return_value = True
        manager_instance.list_endpoints.return_value = [
            {'method': 'GET', 'path': '/users', 'summary': 'Get all users'},
            {'method': 'POST', 'path': '/users', 'summary': 'Create user'}
        ]

        self.mock_args.action = "list"

        # Capture print output
        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                run_api_lab_cli(self.mock_args)

        # Verify calls
        manager_instance.load_spec.assert_called_once()
        manager_instance.list_endpoints.assert_called_once()

        mock_exit.assert_called_with(0)

    @patch("shared.api_lab.ApiLabManager")
    @patch("sys.exit")
    def test_list_command_no_endpoints(self, mock_exit, MockManager):
        mock_exit.side_effect = SystemExit
        manager_instance = MockManager.return_value
        manager_instance.load_spec.return_value = True
        manager_instance.list_endpoints.return_value = []

        self.mock_args.action = "list"

        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                run_api_lab_cli(self.mock_args)

        mock_print.assert_any_call("No endpoints found in spec.")
        mock_exit.assert_called_with(0)

    @patch("shared.api_lab.ApiLabManager")
    @patch("sys.exit")
    def test_run_command_success(self, mock_exit, MockManager):
        mock_exit.side_effect = SystemExit
        manager_instance = MockManager.return_value
        manager_instance.load_spec.return_value = True
        manager_instance.get_server_url.return_value = "http://api.example.com"

        manager_instance.execute_request.return_value = {
            'status_code': 200,
            'headers': {'content-type': 'application/json'},
            'body': '{"id": 1}',
            'success': True
        }

        self.mock_args.action = "run"
        self.mock_args.method = "GET"
        self.mock_args.url = "/users/1"
        self.mock_args.body = None
        self.mock_args.headers = None

        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                run_api_lab_cli(self.mock_args)

        # Verify logic
        manager_instance.get_server_url.assert_called_once()
        manager_instance.execute_request.assert_called_with(
            "GET",
            "http://api.example.com/users/1",
            headers={},
            body=None
        )
        mock_exit.assert_called_with(0)

    @patch("shared.api_lab.ApiLabManager")
    @patch("sys.exit")
    def test_run_command_failure(self, mock_exit, MockManager):
        mock_exit.side_effect = SystemExit
        manager_instance = MockManager.return_value
        manager_instance.load_spec.return_value = True
        manager_instance.execute_request.return_value = {
            'status_code': 404,
            'headers': {},
            'body': 'Not Found',
            'success': False
        }

        self.mock_args.action = "run"
        self.mock_args.method = "GET"
        self.mock_args.url = "http://full.url/api"
        self.mock_args.body = None
        self.mock_args.headers = None

        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                run_api_lab_cli(self.mock_args)

        manager_instance.execute_request.assert_called_with(
            "GET",
            "http://full.url/api",
            headers={},
            body=None
        )
        mock_exit.assert_called_with(1)

    @patch("shared.api_lab.ApiLabManager")
    @patch("sys.exit")
    def test_run_command_with_headers_and_body(self, mock_exit, MockManager):
        mock_exit.side_effect = SystemExit
        manager_instance = MockManager.return_value
        manager_instance.load_spec.return_value = True
        manager_instance.get_server_url.return_value = "http://localhost:8000"

        manager_instance.execute_request.return_value = {
            'status_code': 201,
            'headers': {},
            'body': '{}',
            'success': True
        }

        self.mock_args.action = "run"
        self.mock_args.method = "POST"
        self.mock_args.url = "/users"
        self.mock_args.body = '{"name": "Alice"}'
        self.mock_args.headers = '{"Authorization": "Bearer token"}'

        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                run_api_lab_cli(self.mock_args)

        manager_instance.execute_request.assert_called_with(
            "POST",
            "http://localhost:8000/users",
            headers={"Authorization": "Bearer token"},
            body='{"name": "Alice"}'
        )
        mock_exit.assert_called_with(0)

    @patch("shared.api_lab.ApiLabManager")
    @patch("sys.exit")
    def test_run_command_invalid_headers(self, mock_exit, MockManager):
        mock_exit.side_effect = SystemExit
        self.mock_args.action = "run"
        self.mock_args.method = "GET"
        self.mock_args.url = "/users"
        self.mock_args.body = None
        self.mock_args.headers = "{invalid_json}"

        with patch("builtins.print") as mock_print:
            with self.assertRaises(SystemExit):
                run_api_lab_cli(self.mock_args)

        mock_exit.assert_called_with(1)

if __name__ == "__main__":
    unittest.main()
