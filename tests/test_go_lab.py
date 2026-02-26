import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import subprocess
import requests

# Ensure we can import from shared
sys.path.append(str(Path(__file__).parent.parent))

from shared.go_lab import GoLabManager

class TestGoLab(unittest.TestCase):

    def setUp(self):
        self.manager = GoLabManager()

    @patch('requests.get')
    def test_get_latest_version(self, mock_get):
        # Mock successful JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Version": "v1.2.3", "Time": "2023-01-01T00:00:00Z"}
        mock_get.return_value = mock_response

        info = self.manager.get_latest_version("example.com/foo")
        self.assertEqual(info["Version"], "v1.2.3")

        # Verify correct URL call
        mock_get.assert_called_with("https://proxy.golang.org/example.com/foo/@latest", timeout=10)

    @patch('requests.get')
    def test_get_versions(self, mock_get):
        # Mock successful text response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "v1.0.0\nv1.1.0\nv1.2.0\n"
        mock_get.return_value = mock_response

        versions = self.manager.get_versions("example.com/foo")
        self.assertEqual(versions, ["v1.0.0", "v1.1.0", "v1.2.0"])

        # Verify correct URL call
        mock_get.assert_called_with("https://proxy.golang.org/example.com/foo/@v/list", timeout=10)

    @patch('subprocess.run')
    def test_init_mod(self, mock_run):
        self.manager.init_mod("example.com/my-module")
        mock_run.assert_called_with(["go", "mod", "init", "example.com/my-module"], cwd=self.manager.project_dir, check=True)

    @patch('subprocess.run')
    def test_tidy(self, mock_run):
        self.manager.tidy()
        mock_run.assert_called_with(["go", "mod", "tidy"], cwd=self.manager.project_dir, check=True)

    @patch('subprocess.run')
    def test_install(self, mock_run):
        self.manager.install("example.com/pkg")
        mock_run.assert_called_with(["go", "get", "example.com/pkg"], cwd=self.manager.project_dir, check=True)

    @patch('requests.get')
    def test_get_latest_version_404(self, mock_get):
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as cm:
            self.manager.get_latest_version("example.com/unknown")

        self.assertIn("Resource not found", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
