import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import subprocess
import argparse
import sys
import os

# This is a bit of a hack to import main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import run_review

class TestReviewCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Create a mock git repository
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        (self.project_dir / "test.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.print')
    def test_review_no_completed_file(self, mock_print):
        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_review(args)
        self.assertEqual(cm.exception.code, 0)
        mock_print.assert_any_call("Agent has not marked its work as complete. Nothing to review.")

    @patch('subprocess.run')
    @patch('builtins.print')
    def test_review_tests_fail(self, mock_print, mock_subprocess_run):
        (self.project_dir / "COMPLETED").touch()
        # Mock a failed test run
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="Tests failed", stderr="Error")

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("❌ Tests failed. Review cannot proceed.")

    @patch('builtins.input', return_value='a')
    @patch('subprocess.run')
    def test_review_approve(self, mock_subprocess_run, mock_input):
        (self.project_dir / "COMPLETED").touch()
        # Mock successful test run and other subprocess calls
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.project_dir / "QA_PASSED").exists())

    @patch('builtins.input', side_effect=['r', ''])
    @patch('subprocess.run')
    def test_review_reject(self, mock_subprocess_run, mock_input):
        (self.project_dir / "COMPLETED").touch()
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse((self.project_dir / "COMPLETED").exists())

    @patch('builtins.input', side_effect=['r', 'some feedback'])
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_review_reject_with_feedback(self, mock_print, mock_subprocess_run, mock_input):
        (self.project_dir / "COMPLETED").touch()
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse((self.project_dir / "COMPLETED").exists())
        mock_print.assert_any_call("Feedback recorded. You may want to copy this into a new spec or directive.")

    @patch('builtins.input', side_effect=['s', 'q'])
    @patch('subprocess.run')
    def test_review_shell(self, mock_subprocess_run, mock_input):
        (self.project_dir / "COMPLETED").touch()
        # First call is for tests, second is for shell
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # tests
            MagicMock(returncode=0, stdout="...shell...", stderr=""), # git diff
            MagicMock(returncode=0, stdout="...", stderr=""), # last run id
            MagicMock(returncode=0, stdout="...logs...", stderr=""), # logs
            MagicMock(returncode=0)  # shell
        ]

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        # Check that the shell was called
        shell_call = mock_subprocess_run.call_args_list[-1]
        self.assertEqual(shell_call.args[0], os.environ.get('SHELL', 'bash'))


if __name__ == '__main__':
    unittest.main()
