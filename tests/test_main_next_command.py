import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import tempfile
import shutil
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_next

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Create a dummy .git directory to make it a git repo
        (self.project_dir / ".git").mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    @patch('main.get_suggestions')
    def test_next_command_executes_suggestion(self, mock_get_suggestions, mock_subprocess_run, mock_input):
        # Arrange
        mock_get_suggestions.return_value = [
            {"command": "main.py status", "reason": "Check the status."}
        ]
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)
        executable_path = sys.argv[0]
        expected_command = [executable_path, 'status']
        # Convert Path object to string for comparison
        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.project_dir)

    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    @patch('main.get_suggestions')
    def test_next_command_aborts_on_no(self, mock_get_suggestions, mock_subprocess_run, mock_input):
        # Arrange
        mock_get_suggestions.return_value = [
            {"command": "main.py status", "reason": "Check the status."}
        ]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)
        mock_subprocess_run.assert_not_called()

    @patch('main.get_suggestions')
    def test_next_command_no_suggestions(self, mock_get_suggestions):
        # Arrange
        mock_get_suggestions.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)

if __name__ == '__main__':
    unittest.main()
