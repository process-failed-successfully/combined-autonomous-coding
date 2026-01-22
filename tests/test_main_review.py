
import main
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil
import sys
import io

# Adjust the path to import main
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestReviewCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.completed_file = self.project_dir / "COMPLETED"
        self.qa_passed_file = self.project_dir / "QA_PASSED"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.input', return_value='y')
    @patch('main.run_test')
    @patch('main.run_diff')
    def test_review_approve_success(self, mock_run_diff, mock_run_test, mock_input):
        """Test the review command with successful approval."""
        self.completed_file.touch()
        args = main.parse_args(['review', '--project-dir', str(self.project_dir)])

        with self.assertRaises(SystemExit) as cm:
            main.run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(self.qa_passed_file.exists())
        mock_run_test.assert_called_once()
        mock_run_diff.assert_called_once()

    @patch('builtins.input', return_value='n')
    @patch('main.run_test')
    @patch('main.run_diff')
    def test_review_reject(self, mock_run_diff, mock_run_test, mock_input):
        """Test the review command with rejection."""
        self.completed_file.touch()
        self.assertTrue(self.completed_file.exists())
        args = main.parse_args(['review', '--project-dir', str(self.project_dir)])

        with self.assertRaises(SystemExit) as cm:
            main.run_review(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.qa_passed_file.exists())
        self.assertFalse(self.completed_file.exists())  # Should be removed on rejection
        mock_run_test.assert_called_once()
        mock_run_diff.assert_called_once()

    @patch('main.run_test', side_effect=SystemExit(1))
    def test_review_tests_fail(self, mock_run_test):
        """Test the review command when tests fail."""
        self.completed_file.touch()
        args = main.parse_args(['review', '--project-dir', str(self.project_dir)])

        with self.assertRaises(SystemExit) as cm:
            main.run_review(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertFalse(self.qa_passed_file.exists())
        self.assertTrue(self.completed_file.exists())  # Should NOT be removed on test failure

    def test_review_no_work_to_review(self):
        """Test the review command when the COMPLETED file doesn't exist."""
        # Ensure the COMPLETED file does not exist
        if self.completed_file.exists():
            self.completed_file.unlink()

        args = main.parse_args(['review', '--project-dir', str(self.project_dir)])

        # Capture stdout to check the message
        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            main.run_review(args)

        sys.stdout = sys.__stdout__  # Restore stdout
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("No agent work is currently marked as 'COMPLETED'", captured_output.getvalue())

    def test_review_already_qa_passed(self):
        """Test the review command when QA_PASSED file already exists."""
        self.completed_file.touch()
        self.qa_passed_file.touch()

        args = main.parse_args(['review', '--project-dir', str(self.project_dir)])
        captured_output = io.StringIO()
        sys.stdout = captured_output

        with self.assertRaises(SystemExit) as cm:
            main.run_review(args)

        sys.stdout = sys.__stdout__
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Agent work has already been reviewed and passed QA", captured_output.getvalue())


if __name__ == '__main__':
    unittest.main()
