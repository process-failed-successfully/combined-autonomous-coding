
import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import sys
import os

# Adjust the path to import from the root of the project
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_next

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_run_next_with_suggestion_and_confirmation(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        # Arrange
        mock_get_suggestions.return_value = [{'command': './main.py test', 'reason': 'Tests are pending.'}]
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_subprocess_run.assert_called_once()
        executable_name = os.path.basename(sys.argv[0])
        expected_command = [sys.executable, executable_name, 'test', '--project-dir', str(self.project_dir)]
        mock_subprocess_run.assert_called_with(expected_command, cwd=self.project_dir)

    @patch('main.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_run_next_with_suggestion_and_rejection(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        # Arrange
        mock_get_suggestions.return_value = [{'command': './main.py test', 'reason': 'Tests are pending.'}]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_subprocess_run.assert_not_called()

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    def test_run_next_with_no_suggestion(self, mock_subprocess_run, mock_get_suggestions):
        # Arrange
        mock_get_suggestions.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
