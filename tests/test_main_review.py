import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import tempfile
import shutil
import subprocess
import argparse

# This is a bit of a hack to ensure we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_review

class TestReviewCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Initialize a git repo because the command uses git diff
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir)
        (self.project_dir / "initial_file.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_args(self, yes=False):
        return argparse.Namespace(
            project_dir=self.project_dir,
            yes=yes
        )

    @patch('sys.stdout')
    def test_review_no_completed_file(self, mock_stdout):
        args = self._create_args()
        with self.assertRaises(SystemExit) as cm:
            run_review(args)
        self.assertEqual(cm.exception.code, 0)
        output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)
        self.assertIn("No work is currently marked as 'COMPLETED'", output)

    @patch('subprocess.Popen')
    @patch('main.run_diff_summary')
    @patch('main.run_test')
    @patch('builtins.input', return_value='a')
    def test_review_approve_flow(self, mock_input, mock_run_test, mock_run_diff_summary, mock_popen):
        # Mock Popen to prevent resource warnings
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('', '')
        mock_process.stdout.close.return_value = None
        mock_popen.return_value = mock_process
        # Setup: Create a COMPLETED file
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "new_file.txt").write_text("new content")

        args = self._create_args()
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_run_diff_summary.assert_called_once()
        self.assertEqual(mock_popen.call_count, 2)
        self.assertTrue((self.project_dir / "QA_PASSED").exists())
        self.assertTrue((self.project_dir / "COMPLETED").exists())

    @patch('subprocess.Popen')
    @patch('main.run_diff_summary')
    @patch('main.run_test')
    @patch('builtins.input', return_value='r')
    def test_review_reject_flow(self, mock_input, mock_run_test, mock_run_diff_summary, mock_popen):
        # Mock Popen
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('', '')
        mock_process.stdout.close.return_value = None
        mock_popen.return_value = mock_process
        # Setup: Create a COMPLETED file
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "new_file.txt").write_text("new content")

        args = self._create_args()
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_run_diff_summary.assert_called_once()
        self.assertEqual(mock_popen.call_count, 2)
        self.assertFalse((self.project_dir / "QA_PASSED").exists())
        self.assertFalse((self.project_dir / "COMPLETED").exists())

    @patch('subprocess.Popen')
    @patch('main.run_diff_summary')
    @patch('main.run_test', side_effect=SystemExit(1))
    @patch('builtins.input', return_value='r')
    @patch('sys.stderr')
    def test_review_failing_tests_still_allows_decision(self, mock_stderr, mock_input, mock_run_test, mock_run_diff_summary, mock_popen):
        # Mock Popen
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('', '')
        mock_process.stdout.close.return_value = None
        mock_popen.return_value = mock_process
        (self.project_dir / "COMPLETED").touch()
        args = self._create_args()

        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        self.assertEqual(mock_popen.call_count, 2)
        # Check that we warned the user about failing tests
        output = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
        self.assertIn("Tests failed", output)
        # Check that the rejection was still processed
        self.assertFalse((self.project_dir / "COMPLETED").exists())

    @patch('subprocess.Popen')
    @patch('main.run_diff_summary')
    @patch('main.run_test')
    @patch('builtins.input')
    def test_review_approve_with_yes_flag(self, mock_input, mock_run_test, mock_run_diff_summary, mock_popen):
        # Mock Popen
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('', '')
        mock_process.stdout.close.return_value = None
        mock_popen.return_value = mock_process
        (self.project_dir / "COMPLETED").touch()
        args = self._create_args(yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_not_called()
        self.assertEqual(mock_popen.call_count, 2)
        self.assertTrue((self.project_dir / "QA_PASSED").exists())

if __name__ == '__main__':
    unittest.main()
