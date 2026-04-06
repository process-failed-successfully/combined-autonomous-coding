import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import sys
from io import StringIO
from shared.pre_commit_lab import run_pre_commit_lab_logic

class TestPreCommitCLI(unittest.TestCase):
    def setUp(self):
        self.mock_stdout = StringIO()
        self.mock_stderr = StringIO()
        self.patcher_stdout = patch("sys.stdout", self.mock_stdout)
        self.patcher_stderr = patch("sys.stderr", self.mock_stderr)
        self.patcher_stdout.start()
        self.patcher_stderr.start()

    def tearDown(self):
        self.patcher_stdout.stop()
        self.patcher_stderr.stop()

    @patch("shared.pre_commit_lab.PreCommitLabManager.install")
    def test_install_tool_success(self, mock_install):
        from pathlib import Path
        mock_install.return_value = True
        args = Namespace(project_dir=Path("."), action="install-tool")
        with self.assertRaises(SystemExit) as cm:
            run_pre_commit_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Successfully installed pre-commit", self.mock_stdout.getvalue())

    @patch("shared.pre_commit_lab.PreCommitLabManager.create_default_config")
    def test_create_config_success(self, mock_create):
        from pathlib import Path
        mock_create.return_value = True
        args = Namespace(project_dir=Path("."), action="create-config")
        with self.assertRaises(SystemExit) as cm:
            run_pre_commit_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Successfully created config", self.mock_stdout.getvalue())

    @patch("shared.pre_commit_lab.PreCommitLabManager.run_all_hooks")
    def test_run_all_success(self, mock_run_all):
        from pathlib import Path
        mock_run_all.return_value = (True, "output")
        args = Namespace(project_dir=Path("."), action="run-all")
        with self.assertRaises(SystemExit) as cm:
            run_pre_commit_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Hooks ran successfully", self.mock_stdout.getvalue())

    @patch("shared.pre_commit_lab.PreCommitLabManager.is_installed")
    @patch("shared.pre_commit_lab.PreCommitLabManager.config_exists")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_hooks")
    def test_status(self, mock_get_hooks, mock_config_exists, mock_is_installed):
        from pathlib import Path
        mock_is_installed.return_value = True
        mock_config_exists.return_value = True
        mock_get_hooks.return_value = [{"id": "flake8", "repo": "local", "rev": "1.0"}]
        args = Namespace(project_dir=Path("."), action="status")

        # Status doesn't exit, it just prints
        try:
            run_pre_commit_lab_logic(args)
        except SystemExit:
            pass # Accept if it exits or not

        output = self.mock_stdout.getvalue()
        self.assertIn("Tool: ✅ Installed", output)
        self.assertIn("Config: ✅ Found", output)
        self.assertIn("flake8 (local @ 1.0)", output)

    def test_invalid_action(self):
        from pathlib import Path
        args = Namespace(project_dir=Path("."), action="invalid-action")
        with self.assertRaises(SystemExit) as cm:
            run_pre_commit_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Unknown action", self.mock_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
