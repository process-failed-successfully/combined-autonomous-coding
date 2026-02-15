import unittest
from unittest.mock import patch, MagicMock, mock_open
from shared.pypi_lab import PyPiLabManager, run_pypi_lab_logic
import argparse
import sys
import io
import requests
from pathlib import Path

class TestPyPiLab(unittest.TestCase):
    def setUp(self):
        self.manager = PyPiLabManager()
        self.sample_json = {
            "info": {
                "name": "test-pkg",
                "version": "1.0.0",
                "summary": "A test package",
                "author": "Tester",
                "license": "MIT",
                "home_page": "https://example.com",
                "package_url": "https://pypi.org/project/test-pkg/",
                "project_urls": {"Source": "https://github.com/test/test-pkg"},
                "requires_dist": ["requests (>=2.0.0)", "urllib3"]
            },
            "releases": {
                "1.0.0": [{"upload_time": "2023-01-01T12:00:00"}],
                "0.9.0": [{"upload_time": "2022-01-01T12:00:00"}]
            },
            "urls": [
                {
                    "filename": "test-pkg-1.0.0.tar.gz",
                    "packagetype": "sdist",
                    "url": "https://files.pythonhosted.org/packages/.../test-pkg-1.0.0.tar.gz",
                    "digests": {"sha256": "abcdef1234567890"},
                    "size": 1024
                }
            ]
        }

    @patch("shared.pypi_lab.requests.get")
    def test_get_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        info = self.manager.get_info("test-pkg")
        self.assertEqual(info["name"], "test-pkg")
        self.assertEqual(info["version"], "1.0.0")
        self.assertEqual(info["author"], "Tester")

    @patch("shared.pypi_lab.requests.get")
    def test_get_releases(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        releases = self.manager.get_releases("test-pkg")
        self.assertEqual(len(releases), 2)
        self.assertIn("1.0.0", releases)
        self.assertIn("0.9.0", releases)

    @patch("shared.pypi_lab.requests.get")
    def test_get_dependencies(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        deps = self.manager.get_dependencies("test-pkg")
        self.assertEqual(len(deps), 2)
        self.assertIn("requests (>=2.0.0)", deps)

    @patch("shared.pypi_lab.requests.get")
    def test_get_files(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        files = self.manager.get_files("test-pkg")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["filename"], "test-pkg-1.0.0.tar.gz")

    @patch("shared.pypi_lab.requests.get")
    def test_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError):
            self.manager.get_info("non-existent")

    @patch("shared.pypi_lab.requests.get")
    def test_cli_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        args = argparse.Namespace(action="info", package="test-pkg")

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            run_pypi_lab_logic(args)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("test-pkg 1.0.0", output)
        self.assertIn("A test package", output)

    @patch("shared.pypi_lab.requests.get")
    def test_cli_releases(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        args = argparse.Namespace(action="releases", package="test-pkg")

        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            run_pypi_lab_logic(args)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("2023-01-01", output)
        self.assertIn("1.0.0", output)

    @patch("builtins.open", new_callable=mock_open)
    @patch("shared.pypi_lab.requests.get")
    def test_download(self, mock_get, mock_file):
        # Setup mocks
        mock_resp_json = MagicMock()
        mock_resp_json.json.return_value = self.sample_json
        mock_resp_json.status_code = 200

        mock_resp_file = MagicMock()
        mock_resp_file.status_code = 200
        mock_resp_file.iter_content.return_value = [b"data"]

        # Side effect to return json first (for get_files), then file content (for download)
        mock_get.side_effect = [mock_resp_json, mock_resp_file]

        downloaded = self.manager.download("test-pkg", dest=".")

        self.assertEqual(len(downloaded), 1)
        self.assertTrue(str(downloaded[0]).endswith("test-pkg-1.0.0.tar.gz"))
        mock_file.assert_called_with(Path("test-pkg-1.0.0.tar.gz"), 'wb')

if __name__ == "__main__":
    unittest.main()
