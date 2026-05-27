import unittest
from unittest.mock import patch, MagicMock
import os
import json
import yaml
import tempfile
from pathlib import Path
import sys

# Ensure shared is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.openapi_ui_lab import run_openapi_ui_lab_logic


class TestOpenAPIUILab(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_logic_missing_file(self):
        args = MagicMock()
        args.spec_file = str(self.test_dir / "does_not_exist.yaml")
        args.port = 8080

        with patch('sys.stderr') as mock_stderr:
            result = run_openapi_ui_lab_logic(args)

        self.assertFalse(result)

    def test_run_logic_invalid_yaml(self):
        invalid_yaml_path = self.test_dir / "invalid.yaml"
        invalid_yaml_path.write_text("invalid: yaml: :", encoding="utf-8")

        args = MagicMock()
        args.spec_file = str(invalid_yaml_path)
        args.port = 8080

        with patch('sys.stderr') as mock_stderr:
            result = run_openapi_ui_lab_logic(args)

        self.assertFalse(result)

    @patch('shared.openapi_ui_lab.socketserver.TCPServer')
    @patch('shared.openapi_ui_lab.webbrowser.open')
    def test_run_logic_success_yaml(self, mock_webbrowser, mock_server):
        # Create valid yaml
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0"}}
        valid_yaml_path = self.test_dir / "valid.yaml"
        valid_yaml_path.write_text(yaml.dump(spec_data), encoding="utf-8")

        args = MagicMock()
        args.spec_file = str(valid_yaml_path)
        args.port = 8080

        # Setup mock server
        mock_server_instance = MagicMock()
        # To exit serve_forever we can raise KeyboardInterrupt to simulate user stopping it
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()
        mock_server.return_value.__enter__.return_value = mock_server_instance

        with patch('sys.stdout'):
            result = run_openapi_ui_lab_logic(args)

        self.assertTrue(result)
        mock_webbrowser.assert_called_once_with("http://localhost:8080")
        mock_server_instance.serve_forever.assert_called_once()

    @patch('shared.openapi_ui_lab.socketserver.TCPServer')
    @patch('shared.openapi_ui_lab.webbrowser.open')
    def test_run_logic_success_json(self, mock_webbrowser, mock_server):
        # Create valid json
        spec_data = {"openapi": "3.0.0", "info": {"title": "Test JSON API", "version": "1.0"}}
        valid_json_path = self.test_dir / "valid.json"
        valid_json_path.write_text(json.dumps(spec_data), encoding="utf-8")

        args = MagicMock()
        args.spec_file = str(valid_json_path)
        args.port = 8080

        mock_server_instance = MagicMock()
        # Simulate stopping the server
        mock_server_instance.serve_forever.side_effect = KeyboardInterrupt()
        mock_server.return_value.__enter__.return_value = mock_server_instance

        with patch('sys.stdout'):
            result = run_openapi_ui_lab_logic(args)

        self.assertTrue(result)
        mock_webbrowser.assert_called_once_with("http://localhost:8080")

    @patch('shared.openapi_ui_lab.socketserver.TCPServer')
    def test_run_logic_port_in_use(self, mock_server):
        spec_data = {"openapi": "3.0.0"}
        valid_yaml_path = self.test_dir / "valid2.yaml"
        valid_yaml_path.write_text(yaml.dump(spec_data), encoding="utf-8")

        args = MagicMock()
        args.spec_file = str(valid_yaml_path)
        args.port = 8080

        # Simulate port in use
        os_error = OSError(98, "Address already in use")
        mock_server.side_effect = os_error

        with patch('sys.stderr') as mock_stderr:
            result = run_openapi_ui_lab_logic(args)

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
