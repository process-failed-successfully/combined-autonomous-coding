
import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_next, parse_args

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        # Create a dummy project directory
        self.project_dir = Path("test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)
        (self.project_dir / "test.txt").write_text("initial content")


    def tearDown(self):
        # Clean up the dummy project directory
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('main.run_diff_summary')
    def test_next_executes_suggestion(self, mock_run_diff_summary, mock_input, mock_get_suggestions):
        mock_get_suggestions.return_value = [
            {"command": "main.py diff-summary", "reason": "You have uncommitted changes."}
        ]

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_run_diff_summary.assert_called_once()


    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('main.run_diff_summary')
    def test_next_aborts_on_user_rejection(self, mock_run_diff_summary, mock_input, mock_get_suggestions):
        mock_get_suggestions.return_value = [
            {"command": "main.py diff-summary", "reason": "You have uncommitted changes."}
        ]

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_diff_summary.assert_not_called()

    @patch('main.get_suggestions')
    @patch('main.run_diff_summary')
    def test_next_executes_with_yes_flag(self, mock_run_diff_summary, mock_get_suggestions):
        mock_get_suggestions.return_value = [
            {"command": "main.py diff-summary", "reason": "You have uncommitted changes."}
        ]

        args = argparse.Namespace(project_dir=self.project_dir, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_diff_summary.assert_called_once()

    @patch('main.get_suggestions')
    def test_next_no_suggestions(self, mock_get_suggestions):
        mock_get_suggestions.return_value = []

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)

if __name__ == '__main__':
    unittest.main()
