import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys
from io import StringIO

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_next
from shared.cli_utils import _run_next_logic

class TestNextCommand(unittest.TestCase):

    @patch('main._run_next_logic')
    def test_run_next_calls_logic(self, mock_run_next_logic):
        """Test that the main `run_next` command calls the underlying logic function."""
        args = argparse.Namespace(project_dir=Path("/test/project"))

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_next_logic.assert_called_once_with(project_dir=Path("/test/project"))

    @patch('shared.cli_utils.get_suggestions')
    def test_run_next_logic_no_suggestions(self, mock_get_suggestions):
        """Test the logic when no suggestions are available."""
        mock_get_suggestions.return_value = []

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = _run_next_logic(project_dir=Path("/fake/dir"))
            self.assertTrue(result)
            self.assertIn("No specific next action to suggest", mock_stdout.getvalue())

    @patch('shared.cli_utils.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_run_next_logic_user_confirms_and_succeeds(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test the logic when the user confirms and the command succeeds."""
        mock_get_suggestions.return_value = [
            {"command": "main.py status", "reason": "Check the project status."}
        ]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = _run_next_logic(project_dir=Path("/fake/dir"))
            self.assertTrue(result)
            self.assertIn("--- Executing: main.py status ---", mock_stdout.getvalue())
            self.assertIn("Command finished successfully", mock_stdout.getvalue())
            mock_subprocess_run.assert_called_once()

    @patch('shared.cli_utils.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_run_next_logic_user_declines(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test the logic when the user declines to execute the command."""
        mock_get_suggestions.return_value = [
            {"command": "main.py test", "reason": "Run tests."}
        ]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = _run_next_logic(project_dir=Path("/fake/dir"))
            self.assertTrue(result)
            self.assertIn("Aborted.", mock_stdout.getvalue())
            mock_subprocess_run.assert_not_called()

    @patch('shared.cli_utils.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_run_next_logic_command_fails(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test the logic when the executed command fails."""
        mock_get_suggestions.return_value = [
            {"command": "main.py test", "reason": "Run tests."}
        ]
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = _run_next_logic(project_dir=Path("/fake/dir"))
            self.assertFalse(result)
            self.assertIn("Command finished with an error", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
