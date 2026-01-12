import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path

import main

class TestInteractCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project_interact")
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir, ignore_errors=True)

    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('main.run_diff_summary')
    def test_dynamic_interact_chooses_first_suggestion(self, mock_run_diff_summary, mock_input, mock_get_suggestions):
        """Test that selecting '1' calls the function from the first dynamic suggestion."""
        # Setup mock suggestions
        mock_get_suggestions.return_value = [
            {
                "key": "diff_summary",
                "reason": "You have uncommitted changes. View a summary.",
                "command": "main.py diff-summary",
                "args": {"project_dir": self.project_dir}
            },
            {
                "key": "commit",
                "reason": "Commit your changes.",
                "command": "main.py commit",
                "args": {"project_dir": self.project_dir, "message": None, "run_tests": False}
            }
        ]

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that get_suggestions was called
        mock_get_suggestions.assert_called_with(self.project_dir)

        # Verify that the correct function was called from the suggestion
        mock_run_diff_summary.assert_called_once()
        called_args = mock_run_diff_summary.call_args[0][0]
        self.assertIsInstance(called_args, argparse.Namespace)
        self.assertEqual(called_args.project_dir, self.project_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=['2', 'Test commit', 'q'])
    @patch('main.run_commit')
    def test_dynamic_interact_chooses_commit_and_prompts(self, mock_run_commit, mock_input, mock_get_suggestions):
        """Test that selecting a 'commit' suggestion prompts for a message."""
        mock_get_suggestions.return_value = [
            {
                "key": "diff_summary",
                "reason": "View changes.",
                "command": "main.py diff-summary",
                "args": {"project_dir": self.project_dir}
            },
            {
                "key": "commit",
                "reason": "Commit your changes.",
                "command": "main.py commit",
                "args": {"project_dir": self.project_dir, "message": None, "run_tests": False}
            }
        ]

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)

        # Check that input was called for menu selection, commit message, and quit
        self.assertEqual(mock_input.call_count, 3)

        # Verify that run_commit was called with the entered message
        mock_run_commit.assert_called_once()
        called_args = mock_run_commit.call_args[0][0]
        self.assertEqual(called_args.message, "Test commit")
        self.assertEqual(called_args.project_dir, self.project_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=['q'])
    def test_dynamic_interact_quits(self, mock_input, mock_get_suggestions):
        """Test that 'q' quits the interactive session."""
        mock_get_suggestions.return_value = [] # No suggestions
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_called_once_with("> ")


    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('main.run_test')
    def test_interact_handles_no_suggestions_fallback(self, mock_run_test, mock_input, mock_get_suggestions):
        """Test that default options are shown when get_suggestions returns empty."""
        mock_get_suggestions.return_value = [] # No suggestions

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)

        # The first default option is 'test'
        mock_run_test.assert_called_once()
        called_args = mock_run_test.call_args[0][0]
        self.assertEqual(called_args.project_dir, self.project_dir)
        self.assertEqual(called_args.test_args, [])


    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=['invalid', '1', 'q'])
    @patch('main.run_diff_summary')
    def test_interact_handles_invalid_then_valid_input(self, mock_run_diff_summary, mock_input, mock_get_suggestions):
        """Test that the session continues after invalid (non-numeric) input."""
        mock_get_suggestions.return_value = [
            {
                "key": "diff_summary",
                "reason": "View changes.",
                "command": "main.py diff-summary",
                "args": {"project_dir": self.project_dir}
            }
        ]

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)

        self.assertEqual(mock_input.call_count, 3)
        mock_run_diff_summary.assert_called_once()

    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=['5', 'q']) # Out of bounds
    @patch('main.run_diff_summary')
    def test_interact_handles_out_of_bounds_input(self, mock_run_diff_summary, mock_input, mock_get_suggestions):
        """Test that the session continues after out-of-bounds numeric input."""
        mock_get_suggestions.return_value = [
            {
                "key": "diff_summary",
                "reason": "View changes.",
                "command": "main.py diff-summary",
                "args": {"project_dir": self.project_dir}
            }
        ]

        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)

        self.assertEqual(mock_input.call_count, 2)
        mock_run_diff_summary.assert_not_called()

if __name__ == '__main__':
    unittest.main()