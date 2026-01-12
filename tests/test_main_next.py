import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys
import io

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from pathlib import Path
import argparse
import sys
import io

# Make sure the main module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main

class TestNextCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_next_cmd_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_next_command_accepts_suggestion(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test that the 'next' command executes the suggestion when the user accepts."""
        # Arrange
        executable_name = "main.py"
        mock_get_suggestions.return_value = [{'command': f'{executable_name} status', 'reason': 'Check the status.'}]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = argparse.Namespace(
            project_dir=self.test_dir,
            yes=False
        )

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.test_dir, limit=1)
        mock_input.assert_called_once()

        # Verify that subprocess.run was called with the correct command
        expected_command = [sys.executable, main.__file__, 'status']
        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.test_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_next_command_declines_suggestion(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test that the 'next' command does not execute when the user declines."""
        # Arrange
        mock_get_suggestions.return_value = [{'command': 'main.py status', 'reason': 'Check the status.'}]
        args = argparse.Namespace(
            project_dir=self.test_dir,
            yes=False
        )

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.test_dir, limit=1)
        mock_input.assert_called_once()
        mock_subprocess_run.assert_not_called()

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    def test_next_command_with_yes_flag(self, mock_subprocess_run, mock_get_suggestions):
        """Test that the 'next' command executes automatically with the --yes flag."""
        # Arrange
        executable_name = "main.py"
        mock_get_suggestions.return_value = [{'command': f'{executable_name} test', 'reason': 'Run tests.'}]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = argparse.Namespace(
            project_dir=self.test_dir,
            yes=True
        )

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.test_dir, limit=1)

        expected_command = [sys.executable, main.__file__, 'test']
        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.test_dir)

    @patch('main.get_suggestions', return_value=[])
    @patch('subprocess.run')
    def test_next_command_no_suggestions(self, mock_subprocess_run, mock_get_suggestions):
        """Test the 'next' command's behavior when no suggestions are available."""
        # Arrange
        args = argparse.Namespace(
            project_dir=self.test_dir,
            yes=False
        )

        # Act & Assert
        with self.assertRaises(SystemExit) as cm, \
             patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.test_dir, limit=1)
        mock_subprocess_run.assert_not_called()
        self.assertIn("No specific next action to suggest", mock_stdout.getvalue())

    @patch('main.get_suggestions')
    @patch('builtins.input', side_effect=KeyboardInterrupt)
    @patch('subprocess.run')
    def test_next_command_keyboard_interrupt(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        """Test that the 'next' command exits gracefully on KeyboardInterrupt."""
        # Arrange
        mock_get_suggestions.return_value = [{'command': 'main.py status', 'reason': 'Check status.'}]
        args = argparse.Namespace(
            project_dir=self.test_dir,
            yes=False
        )

        # Act & Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_next(args)

        self.assertEqual(cm.exception.code, 1)
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
