import unittest
from unittest.mock import patch, MagicMock
from shared.npm_lab import NpmLabManager, run_npm_lab_logic
import argparse
import sys
import io
import requests

class TestNpmLab(unittest.TestCase):
    def setUp(self):
        self.manager = NpmLabManager()
        self.sample_json = {
            "name": "test-pkg",
            "description": "A test package",
            "author": {"name": "Tester"},
            "license": "MIT",
            "homepage": "https://example.com",
            "repository": {"url": "git+https://github.com/test/test-pkg.git"},
            "keywords": ["test", "npm"],
            "dist-tags": {
                "latest": "1.0.0",
                "next": "1.1.0-beta"
            },
            "versions": {
                "1.0.0": {
                    "version": "1.0.0",
                    "dependencies": {"react": "^17.0.0"},
                    "devDependencies": {"jest": "^26.0.0"},
                    "peerDependencies": {"lodash": "*"}
                },
                "0.9.0": {
                    "version": "0.9.0"
                }
            },
            "time": {
                "created": "2022-01-01T00:00:00.000Z",
                "modified": "2023-01-01T00:00:00.000Z",
                "1.0.0": "2023-01-01T12:00:00.000Z",
                "0.9.0": "2022-01-01T12:00:00.000Z"
            }
        }
        self.search_json = {
            "objects": [
                {
                    "package": {
                        "name": "search-result",
                        "version": "2.0.0",
                        "description": "Found me",
                        "date": "2023-02-01T10:00:00.000Z",
                        "publisher": {"username": "publisher"}
                    },
                    "score": {"final": 0.9}
                }
            ]
        }

    @patch("shared.npm_lab.requests.get")
    def test_get_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        info = self.manager.get_info("test-pkg")
        self.assertEqual(info["name"], "test-pkg")
        self.assertEqual(info["latest_version"], "1.0.0")
        self.assertEqual(info["author"], "Tester")

    @patch("shared.npm_lab.requests.get")
    def test_get_versions(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        versions = self.manager.get_versions("test-pkg")
        self.assertEqual(len(versions), 2)
        # Should be sorted by date descending (1.0.0 is 2023, 0.9.0 is 2022)
        self.assertEqual(versions[0]["version"], "1.0.0")
        self.assertEqual(versions[1]["version"], "0.9.0")

    @patch("shared.npm_lab.requests.get")
    def test_get_dependencies(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        deps = self.manager.get_dependencies("test-pkg")
        self.assertEqual(deps["dependencies"]["react"], "^17.0.0")
        self.assertEqual(deps["devDependencies"]["jest"], "^26.0.0")

    @patch("shared.npm_lab.requests.get")
    def test_get_dist_tags(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        tags = self.manager.get_dist_tags("test-pkg")
        self.assertEqual(tags["latest"], "1.0.0")
        self.assertEqual(tags["next"], "1.1.0-beta")

    @patch("shared.npm_lab.requests.get")
    def test_search(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.search_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        results = self.manager.search("query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "search-result")

    @patch("shared.npm_lab.requests.get")
    def test_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError):
            self.manager.get_info("non-existent")

    @patch("shared.npm_lab.requests.get")
    def test_cli_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        args = argparse.Namespace(action="info", package="test-pkg")

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            run_npm_lab_logic(args)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("test-pkg 1.0.0", output)
        self.assertIn("A test package", output)

if __name__ == "__main__":
    unittest.main()
