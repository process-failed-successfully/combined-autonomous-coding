import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import argparse
from io import StringIO
import sys

# Add project root to path to allow imports from shared and main
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.commands import run_next
import main


class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', return_value='y')
    @patch('main.run_status')
    @patch('shared.cli_utils.get_suggestions')
    def test_next_suggests_and_runs_command(self, mock_get_suggestions, mock_run_status, mock_input, mock_stdout):
        # Arrange
        mock_get_suggestions.return_value = [{
            "command": "main.py status",
            "reason": "To check the project status."
        }]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args, main)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_run_status.assert_called_once()
        output = mock_stdout.getvalue()
        self.assertIn("Suggested command: `main.py status`", output)
        self.assertIn("Reason: To check the project status.", output)
        self.assertIn("--- Executing: `main.py status` ---", output)
        self.assertIn("finished successfully", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', return_value='n')
    @patch('main.run_status')
    @patch('shared.cli_utils.get_suggestions')
    def test_next_aborts_on_user_rejection(self, mock_get_suggestions, mock_run_status, mock_input, mock_stdout):
        # Arrange
        mock_get_suggestions.return_value = [{
            "command": "main.py status",
            "reason": "To check the project status."
        }]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args, main)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_run_status.assert_not_called()
        self.assertIn("Aborted.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('shared.cli_utils.get_suggestions')
    def test_next_no_suggestions(self, mock_get_suggestions, mock_stdout):
        # Arrange
        mock_get_suggestions.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args, main)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("✅ Project is in a clean state. No specific action to suggest.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', return_value='y')
    @patch('main.run_revert')
    @patch('shared.cli_utils.get_suggestions')
    def test_next_handles_commands_with_args(self, mock_get_suggestions, mock_run_revert, mock_input, mock_stdout):
        # Arrange
        mock_get_suggestions.return_value = [{
            "command": "main.py revert --interactive",
            "reason": "To discard unwanted changes."
        }]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit):
            run_next(args, main)

        # Assert
        mock_run_revert.assert_called_once()
        # Check that the parsed args for the called command are correct
        called_args = mock_run_revert.call_args[0][0]
        self.assertTrue(called_args.interactive)
        self.assertEqual(called_args.project_dir, self.project_dir)


if __name__ == '__main__':
    unittest.main()