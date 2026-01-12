import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import sys
import io
from contextlib import redirect_stdout

# It's better to import the module directly for easier patching and inspection
import main

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_next_command_happy_path(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test the 'next' command when the user accepts the suggestion."""
        mock_get_suggestions.return_value = [{
            "command": "main.py status",
            "reason": "You have uncommitted changes."
        }]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        # Construct the arguments for the run_next function
        args = MagicMock()
        args.project_dir = self.project_dir
        args.yes = False

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify that get_suggestions was called correctly
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)

        # Verify that the user was prompted for confirmation
        mock_input.assert_called_once()

        # Verify that the suggested command was executed
        mock_subprocess_run.assert_called_once()
        # Check the command that was run
        executed_command = mock_subprocess_run.call_args[0][0]
        self.assertIn(sys.executable, executed_command[0])
        self.assertIn('main.py', executed_command[1])
        self.assertEqual(executed_command[2], 'status')


    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_next_command_user_aborts(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test the 'next' command when the user rejects the suggestion."""
        mock_get_suggestions.return_value = [{
            "command": "main.py status",
            "reason": "You have uncommitted changes."
        }]

        args = MagicMock()
        args.project_dir = self.project_dir
        args.yes = False

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify that get_suggestions was called
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)

        # Verify that the user was prompted
        mock_input.assert_called_once()

        # Verify that the command was NOT executed
        mock_subprocess_run.assert_not_called()

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    def test_next_command_no_suggestions(self, mock_subprocess_run, mock_get_suggestions):
        """Test the 'next' command when there are no suggestions."""
        mock_get_suggestions.return_value = []

        args = MagicMock()
        args.project_dir = self.project_dir
        args.yes = False

        # Capture stdout to check the output message
        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                main.run_next(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify that get_suggestions was called
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)

        # Verify that the command was NOT executed
        mock_subprocess_run.assert_not_called()

        # Check the output message
        output = f.getvalue()
        self.assertIn("Project is in a clean state", output)

    @patch('main.get_suggestions')
    @patch('builtins.input')
    @patch('subprocess.run')
    def test_next_command_with_yes_flag(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test the 'next' command with the --yes flag skips confirmation."""
        mock_get_suggestions.return_value = [{
            "command": "main.py diff",
            "reason": "You have changes to review."
        }]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = MagicMock()
        args.project_dir = self.project_dir
        args.yes = True

        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify get_suggestions was called
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)

        # Verify that the user was NOT prompted for input
        mock_input.assert_not_called()

        # Verify that the command was executed
        mock_subprocess_run.assert_called_once()
        executed_command = mock_subprocess_run.call_args[0][0]
        self.assertIn('diff', executed_command)

if __name__ == '__main__':
    unittest.main()
