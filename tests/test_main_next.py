import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse

from main import run_next

class TestNextCommand(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch('main.get_next_action')
    @patch('builtins.input', return_value='y')
    @patch('main.parse_args')
    @patch('main.run_diff_summary')
    def test_run_next_with_uncommitted_changes(self, mock_run_diff_summary, mock_parse_args, mock_input, mock_get_next_action):
        # Arrange
        mock_get_next_action.return_value = {
            "command": "main.py diff-summary",
            "reason": "You have uncommitted changes.",
            "args": ["diff-summary"]
        }
        mock_parse_args.return_value = argparse.Namespace(command="diff-summary", project_dir=self.project_dir)
        mock_run_diff_summary.side_effect = SystemExit(0)

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        mock_get_next_action.assert_called_once_with(self.project_dir)
        mock_input.assert_called_once()
        mock_parse_args.assert_called_once_with(["diff-summary"])
        mock_run_diff_summary.assert_called_once_with(mock_parse_args.return_value)
        self.assertEqual(cm.exception.code, 0)

    @patch('main.get_next_action')
    def test_run_next_with_no_suggestions(self, mock_get_next_action):
        # Arrange
        mock_get_next_action.return_value = None
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        mock_get_next_action.assert_called_once_with(self.project_dir)
        self.assertEqual(cm.exception.code, 0)

    @patch('main.get_next_action')
    @patch('builtins.input', return_value='y')
    @patch('main.parse_args')
    @patch('main.run_workflow')
    def test_run_next_to_advance_workflow(self, mock_run_workflow, mock_parse_args, mock_input, mock_get_next_action):
        # Arrange
        mock_get_next_action.return_value = {
            "command": "main.py workflow advance",
            "reason": "The agent has completed its work.",
            "args": ["workflow", "advance"]
        }
        mock_parse_args.return_value = argparse.Namespace(command="workflow", action="advance", project_dir=self.project_dir, yes=False)
        mock_run_workflow.side_effect = SystemExit(0)
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        mock_get_next_action.assert_called_once_with(self.project_dir)
        mock_input.assert_called_once()
        mock_parse_args.assert_called_once_with(["workflow", "advance"])
        mock_run_workflow.assert_called_once_with(mock_parse_args.return_value)
        self.assertEqual(cm.exception.code, 0)

    @patch('main.get_next_action')
    @patch('main.parse_args')
    @patch('main.run_diff_summary')
    def test_run_next_with_yes_flag(self, mock_run_diff_summary, mock_parse_args, mock_get_next_action):
        # Arrange
        mock_get_next_action.return_value = {
            "command": "main.py diff-summary",
            "reason": "You have uncommitted changes.",
            "args": ["diff-summary"]
        }
        mock_parse_args.return_value = argparse.Namespace(command="diff-summary", project_dir=self.project_dir)
        mock_run_diff_summary.side_effect = SystemExit(0)
        args = argparse.Namespace(project_dir=self.project_dir, yes=True)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        mock_get_next_action.assert_called_once_with(self.project_dir)
        mock_parse_args.assert_called_once_with(["diff-summary"])
        mock_run_diff_summary.assert_called_once_with(mock_parse_args.return_value)
        self.assertEqual(cm.exception.code, 0)

    @patch('main.get_next_action')
    @patch('builtins.input', return_value='y')
    @patch('main.parse_args')
    @patch('main.run_diff_summary')
    def test_run_next_propagates_project_dir(self, mock_run_diff_summary, mock_parse_args, mock_input, mock_get_next_action):
        # Arrange
        custom_project_dir = Path("/custom/path")
        mock_get_next_action.return_value = {
            "command": "main.py diff-summary",
            "reason": "You have uncommitted changes.",
            "args": ["diff-summary"]
        }
        # Simulate the parsing of the subcommand arguments
        sub_command_args = argparse.Namespace(command="diff-summary", project_dir=self.project_dir)
        mock_parse_args.return_value = sub_command_args
        mock_run_diff_summary.side_effect = SystemExit(0)

        args = argparse.Namespace(project_dir=custom_project_dir, yes=False)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        # Check that the project_dir on the subcommand's args was updated
        self.assertEqual(sub_command_args.project_dir, custom_project_dir)
        mock_run_diff_summary.assert_called_once_with(sub_command_args)
        self.assertEqual(cm.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
