import unittest
import sys
import os
import json
import argparse
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

# Important: Mock sys.exit with SystemExit(0) exception logic when testing commands that exit 0
from shared.har_lab import HarLabManager, run_har_lab_logic
from main import run_har_lab

class TestHarLab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path(".")
        self.manager = HarLabManager(self.project_dir)
        self.valid_har_path = Path("test_valid.har")

        self.sample_data = {
            "log": {
                "entries": [
                    {
                        "request": {
                            "method": "GET",
                            "url": "https://example.com/api/data",
                            "headers": [
                                {"name": "Accept", "value": "application/json"}
                            ]
                        },
                        "response": {
                            "status": 200,
                            "content": {
                                "mimeType": "application/json",
                                "size": 128,
                                "text": '{"success": true}'
                            }
                        },
                        "time": 45.0
                    },
                    {
                        "request": {
                            "method": "POST",
                            "url": "https://example.com/api/submit",
                            "headers": [
                                {"name": "Content-Type", "value": "application/x-www-form-urlencoded"}
                            ],
                            "postData": {
                                "mimeType": "application/x-www-form-urlencoded",
                                "text": "key=value&id=1"
                            }
                        },
                        "response": {
                            "status": 201,
                            "content": {
                                "mimeType": "text/html",
                                "size": 0
                            }
                        },
                        "time": 120.0
                    }
                ]
            }
        }

        with open(self.valid_har_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_data, f)

    def tearDown(self):
        if self.valid_har_path.exists():
            self.valid_har_path.unlink()

    def test_manager_parse_valid(self):
        data = self.manager._parse_har(self.valid_har_path)
        self.assertIn("log", data)
        self.assertEqual(len(data["log"]["entries"]), 2)

    def test_manager_parse_invalid(self):
        invalid_path = Path("test_invalid.har")
        with open(invalid_path, 'w', encoding='utf-8') as f:
            f.write("not json")

        with self.assertRaises(ValueError):
            self.manager._parse_har(invalid_path)

        invalid_path.unlink()

    def test_manager_summary(self):
        summary = self.manager.summarize(self.valid_har_path)
        self.assertEqual(len(summary), 2)
        self.assertEqual(summary[0]["method"], "GET")
        self.assertEqual(summary[0]["status"], 200)
        self.assertEqual(summary[1]["method"], "POST")

    def test_manager_extract_urls(self):
        urls = self.manager.extract_urls(self.valid_har_path)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://example.com/api/data")

        # Filter GET
        get_urls = self.manager.extract_urls(self.valid_har_path, filter_method="GET")
        self.assertEqual(len(get_urls), 1)
        self.assertEqual(get_urls[0], "https://example.com/api/data")

    def test_manager_generate_curl_get(self):
        curl = self.manager.generate_curl(self.valid_har_path, entry_index=0)
        self.assertIn("curl -X GET 'https://example.com/api/data'", curl)
        self.assertIn("-H 'Accept: application/json'", curl)
        self.assertNotIn("-d", curl)

    def test_manager_generate_curl_post(self):
        curl = self.manager.generate_curl(self.valid_har_path, entry_index=1)
        self.assertIn("curl -X POST 'https://example.com/api/submit'", curl)
        self.assertIn("-H 'Content-Type: application/x-www-form-urlencoded'", curl)
        self.assertIn("-d 'key=value&id=1'", curl)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_summary_action(self, mock_stdout):
        args = argparse.Namespace(action="summary", file=str(self.valid_har_path), project_dir=self.project_dir)
        with patch('sys.exit', side_effect=SystemExit(0)):
            try:
                run_har_lab_logic(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("Total Requests: 2", output)
        self.assertIn("GET", output)
        self.assertIn("POST", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_urls_action(self, mock_stdout):
        args = argparse.Namespace(action="urls", file=str(self.valid_har_path), method="POST", project_dir=self.project_dir)
        with patch('sys.exit', side_effect=SystemExit(0)):
            try:
                run_har_lab_logic(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, "https://example.com/api/submit")

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_curl_action(self, mock_stdout):
        args = argparse.Namespace(action="curl", file=str(self.valid_har_path), index=0, project_dir=self.project_dir)
        with patch('sys.exit', side_effect=SystemExit(0)):
            try:
                run_har_lab_logic(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("curl -X GET 'https://example.com/api/data'", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_har_lab_tui(self, mock_stdout):
        args = argparse.Namespace(action="tui", project_dir=self.project_dir)

        # Patch AgentTUI specifically at the point it's imported locally
        with patch('shared.tui.AgentTUI') as mock_agent_tui:
            mock_app = MagicMock()
            mock_agent_tui.return_value = mock_app

            with patch('sys.exit', side_effect=SystemExit(0)):
                try:
                    run_har_lab(args)
                except SystemExit as e:
                    self.assertEqual(e.code, 0)

            mock_agent_tui.assert_called_once_with(project_dir=self.project_dir, start_tab="tab-har")
            mock_app.run.assert_called_once()
            self.assertIn("Launching HAR Lab TUI...", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
