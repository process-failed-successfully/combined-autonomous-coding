
import unittest
from unittest.mock import patch, call, MagicMock
from pathlib import Path
import subprocess
import argparse
import sys
import shutil

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_commit, run_test

class TestRunCommit(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("test_project").resolve()
        self.project_dir.mkdir(exist_ok=True)
        self.git_path = shutil.which("git")
        if not self.git_path:
            self.fail("Git executable not found in PATH")
        subprocess.run([self.git_path, "init"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("main.run_test")
    @patch("subprocess.run")
    @patch("builtins.input", side_effect=["feat", "cli", "Add new feature", "", "n", "y"])
    def test_run_commit_interactive_mode(self, mock_input, mock_subprocess_run, mock_run_test):
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message=None,
            run_tests=False
        )

        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
            MagicMock(returncode=0, stdout="Commit successful")
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        expected_commit_message = "feat(cli): Add new feature"

        expected_calls = [
            call([self.git_path, "-C", str(self.project_dir), "add", "-A"], check=True, capture_output=True, text=True),
            call([self.git_path, "-C", str(self.project_dir), "diff", "--cached", "--quiet"], capture_output=True),
            call([self.git_path, "-C", str(self.project_dir), "commit", "-m", expected_commit_message], check=True, capture_output=True, text=True),
        ]
        mock_subprocess_run.assert_has_calls(expected_calls, any_order=False)
        mock_run_test.assert_not_called()

    @patch("main.run_test")
    @patch("subprocess.run")
    def test_run_commit_with_message(self, mock_subprocess_run, mock_run_test):
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit message",
            run_tests=False
        )

        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
            MagicMock(returncode=0, stdout="Commit successful")
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        expected_calls = [
            call([self.git_path, "-C", str(self.project_dir), "add", "-A"], check=True, capture_output=True, text=True),
            call([self.git_path, "-C", str(self.project_dir), "diff", "--cached", "--quiet"], capture_output=True),
            call([self.git_path, "-C", str(self.project_dir), "commit", "-m", "Test commit message"], check=True, capture_output=True, text=True)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls)
        mock_run_test.assert_not_called()

    @patch("main.run_test")
    @patch("subprocess.run")
    def test_run_commit_with_run_tests_flag_success(self, mock_subprocess_run, mock_run_test):
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit with tests",
            run_tests=True
        )

        mock_run_test.return_value = None
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1),
            MagicMock(returncode=0, stdout="Commit successful")
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        mock_run_test.assert_called_once()
        self.assertGreaterEqual(mock_subprocess_run.call_count, 3)


    @patch("main.run_test")
    @patch("subprocess.run")
    def test_run_commit_with_run_tests_flag_failure(self, mock_subprocess_run, mock_run_test):
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit with failing tests",
            run_tests=True
        )

        mock_run_test.side_effect = SystemExit(1)
        # We need to mock the `add` call since it will happen before the test run
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 1)

        mock_run_test.assert_called_once()
        mock_subprocess_run.assert_called_once_with([self.git_path, "-C", str(self.project_dir), "add", "-A"], check=True, capture_output=True, text=True)


    @patch("subprocess.run")
    def test_no_changes_to_commit(self, mock_subprocess_run):
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit",
            run_tests=False
        )

        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        mock_subprocess_run.assert_has_calls([
            call([self.git_path, "-C", str(self.project_dir), "add", "-A"], check=True, capture_output=True, text=True),
            call([self.git_path, "-C", str(self.project_dir), "diff", "--cached", "--quiet"], capture_output=True)
        ])
        self.assertEqual(mock_subprocess_run.call_count, 2)

if __name__ == "__main__":
    unittest.main()
