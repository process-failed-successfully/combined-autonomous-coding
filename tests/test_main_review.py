
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import tempfile
import shutil
import argparse

# Add the parent directory to the Python path to allow importing from 'main'
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_review

class TestMainReview(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        (self.project_dir / ".git").mkdir()
        self.completed_marker = self.project_dir / "COMPLETED"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.run_test')
    @patch('main.run_diff')
    @patch('builtins.input', return_value='y')
    def test_review_approve_happy_path(self, mock_input, mock_run_diff, mock_run_test):
        # Arrange
        self.completed_marker.touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_run_diff.assert_called_once()
        mock_input.assert_called_once()
        self.assertFalse(self.completed_marker.exists())
        self.assertTrue((self.project_dir / "QA_PASSED").exists())

    @patch('main.run_test')
    @patch('main.run_diff')
    @patch('builtins.input', return_value='n')
    def test_review_reject_changes(self, mock_input, mock_run_diff, mock_run_test):
        # Arrange
        self.completed_marker.touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        mock_run_diff.assert_called_once()
        mock_input.assert_called_once()
        self.assertFalse(self.completed_marker.exists())
        self.assertFalse((self.project_dir / "QA_PASSED").exists())

    @patch('main.run_test', side_effect=SystemExit(1))
    @patch('main.run_diff')
    @patch('builtins.input')
    def test_review_tests_fail(self, mock_input, mock_run_diff, mock_run_test):
        # Arrange
        self.completed_marker.touch()
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        mock_run_test.assert_called_once()
        mock_run_diff.assert_not_called()
        mock_input.assert_not_called()
        self.assertTrue(self.completed_marker.exists())
        self.assertFalse((self.project_dir / "QA_PASSED").exists())

    def test_review_no_completed_file(self):
        # Arrange
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        self.assertFalse((self.project_dir / "QA_PASSED").exists())

if __name__ == '__main__':
    unittest.main()
