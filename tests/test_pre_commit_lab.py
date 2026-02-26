import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.pre_commit_lab import PreCommitLabManager
import shutil
import subprocess

class TestPreCommitLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/mock/project")
        self.manager = PreCommitLabManager(self.project_dir)

    @patch("shutil.which")
    def test_is_installed(self, mock_which):
        mock_which.return_value = "/usr/bin/pre-commit"
        self.assertTrue(self.manager.is_installed())

        mock_which.return_value = None
        self.assertFalse(self.manager.is_installed())

    @patch("pathlib.Path.exists")
    def test_config_exists(self, mock_exists):
        mock_exists.return_value = True
        self.assertTrue(self.manager.config_exists())

        mock_exists.return_value = False
        self.assertFalse(self.manager.config_exists())

    @patch("subprocess.run")
    def test_install(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.manager.install())

        # Test failure case by mocking subprocess.run raising CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(1, ["pip", "install"])
        self.assertFalse(self.manager.install())

    @patch("builtins.open", new_callable=mock_open)
    def test_create_default_config(self, mock_file):
        self.assertTrue(self.manager.create_default_config())
        mock_file.assert_called_with(self.manager.config_path, "w")

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_get_config_content(self, mock_exists, mock_read):
        mock_exists.return_value = True
        mock_read.return_value = "content"
        self.assertEqual(self.manager.get_config_content(), "content")

        mock_exists.return_value = False
        self.assertEqual(self.manager.get_config_content(), "")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_commands(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/pre-commit"
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        success, output = self.manager.install_hooks()
        self.assertTrue(success)
        self.assertIn("Success", output)
        mock_run.assert_called_with(["pre-commit", "install"], cwd=self.project_dir, capture_output=True, text=True, check=False)

        success, output = self.manager.run_all_hooks()
        self.assertTrue(success)
        mock_run.assert_called_with(["pre-commit", "run", "--all-files"], cwd=self.project_dir, capture_output=True, text=True, check=False)

        success, output = self.manager.autoupdate_hooks()
        self.assertTrue(success)
        mock_run.assert_called_with(["pre-commit", "autoupdate"], cwd=self.project_dir, capture_output=True, text=True, check=False)

    @patch("builtins.open", new_callable=mock_open, read_data="repos:\n  - repo: local\n    hooks:\n      - id: test-hook")
    @patch("pathlib.Path.exists")
    def test_get_hooks(self, mock_exists, mock_file):
        mock_exists.return_value = True
        hooks = self.manager.get_hooks()
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0]["id"], "test-hook")
        self.assertEqual(hooks[0]["repo"], "local")

if __name__ == "__main__":
    unittest.main()
