
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import argparse
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_review

class TestRunReview(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory to act as the project directory."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _get_default_args(self):
        """Helper to create a default args namespace."""
        return argparse.Namespace(project_dir=self.project_dir)

    def test_review_aborts_if_completed_file_missing(self):
        """Test that review command exits if COMPLETED file is not found."""
        args = self._get_default_args()

        with redirect_stdout(StringIO()) as stdout, self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("`COMPLETED` file not found", stdout.getvalue())

    @patch('main.run_test')
    def test_review_aborts_if_tests_fail(self, mock_run_test):
        """Test that review command exits if tests fail."""
        # Simulate test failure by raising SystemExit with a non-zero code
        mock_run_test.side_effect = SystemExit(1)

        # Create the COMPLETED marker file
        (self.project_dir / "COMPLETED").touch()

        args = self._get_default_args()

        with redirect_stderr(StringIO()) as stderr, self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run_test.assert_called_once()
        self.assertIn("Tests failed. The agent's work is not ready for review.", stderr.getvalue())

    @patch('builtins.input', return_value='y')
    @patch('main.run_diff', return_value=None)
    @patch('main.run_test')
    def test_review_approval_flow(self, mock_run_test, mock_run_diff, mock_input):
        """Test the full approval flow: creates QA_PASSED file."""
        # Simulate test success (run_test does nothing and doesn't exit)
        mock_run_test.return_value = None

        # Create the COMPLETED marker file
        (self.project_dir / "COMPLETED").touch()
        qa_passed_marker = self.project_dir / "QA_PASSED"

        self.assertFalse(qa_passed_marker.exists())

        args = self._get_default_args()

        with redirect_stdout(StringIO()) as stdout, self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_run_diff.assert_called_once()
        mock_input.assert_called_once()

        self.assertTrue(qa_passed_marker.exists())
        self.assertIn("Approved! The `QA_PASSED` marker has been created.", stdout.getvalue())

    @patch('builtins.input', return_value='n')
    @patch('main.run_diff', return_value=None)
    @patch('main.run_test')
    def test_review_rejection_flow(self, mock_run_test, mock_run_diff, mock_input):
        """Test the rejection flow: removes COMPLETED file."""
        mock_run_test.return_value = None

        completed_marker = self.project_dir / "COMPLETED"
        completed_marker.touch()
        qa_passed_marker = self.project_dir / "QA_PASSED"

        self.assertTrue(completed_marker.exists())

        args = self._get_default_args()

        with redirect_stdout(StringIO()) as stdout, self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_run_diff.assert_called_once()
        mock_input.assert_called_once()

        self.assertFalse(completed_marker.exists())
        self.assertFalse(qa_passed_marker.exists()) # Ensure it wasn't created
        self.assertIn("Rejected. The `COMPLETED` marker has been removed.", stdout.getvalue())

    @patch('builtins.input', side_effect=['maybe', 'y'])
    @patch('main.run_diff', return_value=None)
    @patch('main.run_test')
    def test_review_handles_invalid_input_then_approves(self, mock_run_test, mock_run_diff, mock_input):
        """Test that the command re-prompts after invalid input and then approves."""
        mock_run_test.return_value = None

        (self.project_dir / "COMPLETED").touch()
        qa_passed_marker = self.project_dir / "QA_PASSED"

        self.assertFalse(qa_passed_marker.exists())

        args = self._get_default_args()

        with redirect_stdout(StringIO()) as stdout, self.assertRaises(SystemExit) as cm:
            run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_input.call_count, 2)
        self.assertTrue(qa_passed_marker.exists())
        self.assertIn("Invalid input. Please enter 'y' for yes or 'n' for no.", stdout.getvalue())
        self.assertIn("Approved!", stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
