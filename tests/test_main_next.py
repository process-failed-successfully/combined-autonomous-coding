import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import io
import sys

# Ensure the main script can be imported
from main import run_next

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        # Redirect stdout to capture print statements
        self.stdout_capture = io.StringIO()
        self.stderr_capture = io.StringIO()
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        self.project_dir = Path("/tmp/test_project")

    def tearDown(self):
        # Restore stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    @patch('main.run_commit')
    @patch('builtins.input', side_effect=['y', 'Test commit message'])
    @patch('shared.cli_utils.get_suggestions')
    def test_next_suggests_and_executes_commit(self, mock_get_suggestions, mock_input, mock_run_commit):
        # Arrange
        mock_get_suggestions.return_value = [{
            "command": "./main.py commit",
            "reason": "You have uncommitted changes."
        }]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)

        # Verify output
        output = self.stdout_capture.getvalue()
        self.assertIn("Suggested next step: You have uncommitted changes.", output)
        self.assertIn("👉 `./main.py commit`", output)
        self.assertIn("--- Executing: ./main.py commit ---", output)

        # Verify that run_commit was called with the correct arguments
        mock_run_commit.assert_called_once()
        call_args = mock_run_commit.call_args[0][0]
        self.assertEqual(call_args.message, "Test commit message")
        self.assertEqual(call_args.project_dir, self.project_dir)

    @patch('main.run_push')
    @patch('builtins.input', return_value='y')
    @patch('shared.cli_utils.get_suggestions')
    def test_next_suggests_and_executes_push(self, mock_get_suggestions, mock_input, mock_run_push):
        # Arrange
        mock_get_suggestions.return_value = [{
            "command": "./main.py push",
            "reason": "Your current branch has not been pushed."
        }]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)

        output = self.stdout_capture.getvalue()
        self.assertIn("Suggested next step: Your current branch has not been pushed.", output)
        self.assertIn("👉 `./main.py push`", output)

        mock_run_push.assert_called_once_with(argparse.Namespace(project_dir=self.project_dir))

    @patch('main.run_commit')
    @patch('builtins.input', return_value='n')
    @patch('shared.cli_utils.get_suggestions')
    def test_next_aborts_if_user_declines(self, mock_get_suggestions, mock_input, mock_run_commit):
        # Arrange
        mock_get_suggestions.return_value = [{
            "command": "./main.py commit",
            "reason": "You have uncommitted changes."
        }]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        output = self.stdout_capture.getvalue()
        self.assertIn("Aborted.", output)
        mock_run_commit.assert_not_called()

    @patch('shared.cli_utils.get_suggestions')
    def test_next_handles_no_suggestions(self, mock_get_suggestions):
        # Arrange
        mock_get_suggestions.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        output = self.stdout_capture.getvalue()
        self.assertIn("Project is in a clean state.", output)

if __name__ == '__main__':
    unittest.main()
