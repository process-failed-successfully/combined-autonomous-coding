import unittest
from unittest.mock import patch, MagicMock
from shared.pypi_lab import PyPiLabManager, run_pypi_lab_logic
import argparse
import sys
import io

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
                "requires_dist": ["requests", "numpy"]
            },
            "releases": {
                "1.0.0": [{"upload_time": "2023-01-01T12:00:00"}],
                "0.9.0": [{"upload_time": "2022-01-01T12:00:00"}]
            },
            "urls": [
                {"filename": "test-pkg-1.0.0.whl", "url": "http://example.com/wheel", "size": 1024, "packagetype": "bdist_wheel"},
                {"filename": "test-pkg-1.0.0.tar.gz", "url": "http://example.com/sdist", "size": 512, "packagetype": "sdist"}
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

    @patch("shared.pypi_lab.requests.get")
    def test_get_releases(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        releases = self.manager.get_releases("test-pkg")
        self.assertIn("1.0.0", releases)
        self.assertIn("0.9.0", releases)

    @patch("shared.pypi_lab.requests.get")
    def test_get_deps(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        deps = self.manager.get_dependencies("test-pkg")
        self.assertEqual(deps, ["requests", "numpy"])

    @patch("shared.pypi_lab.requests.get")
    def test_get_files(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        files = self.manager.get_files("test-pkg")
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["filename"], "test-pkg-1.0.0.whl")

    @patch("shared.pypi_lab.requests.get")
    @patch("builtins.open", new_callable=MagicMock)
    def test_download(self, mock_open, mock_get):
        # Mock API response for metadata
        mock_resp_meta = MagicMock()
        mock_resp_meta.json.return_value = self.sample_json
        mock_resp_meta.status_code = 200

        # Mock download response content
        mock_resp_file = MagicMock()
        mock_resp_file.status_code = 200
        mock_resp_file.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_resp_file.__enter__.return_value = mock_resp_file
        mock_resp_file.__exit__.return_value = None

        # Determine behavior based on URL
        def side_effect(url, **kwargs):
            if "json" in url:
                return mock_resp_meta
            else:
                return mock_resp_file

        mock_get.side_effect = side_effect

        # Mock file write
        mock_file_handle = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_handle

        downloaded = self.manager.download("test-pkg", dest=".")
        self.assertEqual(len(downloaded), 2)
        self.assertTrue(mock_open.called)

    @patch("shared.pypi_lab.requests.get")
    def test_cli_info(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self.sample_json
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        args = argparse.Namespace(action="info", package="test-pkg")

        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            run_pypi_lab_logic(args)
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue()
        self.assertIn("test-pkg 1.0.0", output)
        self.assertIn("A test package", output)

if __name__ == "__main__":
    unittest.main()
