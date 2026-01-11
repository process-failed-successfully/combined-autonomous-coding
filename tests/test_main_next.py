import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
from pathlib import Path
import os
import tempfile
import shutil

# Make sure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.cli_utils import _run_next_logic

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # To make shlex.split work correctly with main.py in tests
        self.main_py_path = Path(__file__).parent.parent / "main.py"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shared.cli_utils.get_suggestions')
    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_next_command_accepts_suggestion(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        mock_get_suggestions.return_value = [
            {"command": "main.py diff-summary", "reason": "You have uncommitted changes."}
        ]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        _run_next_logic(self.project_dir, yes=False)

        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)
        mock_input.assert_called_once()
        expected_command = [sys.executable, str(self.main_py_path.resolve()), 'diff-summary']
        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.project_dir)

    @patch('shared.cli_utils.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_next_command_declines_suggestion(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        mock_get_suggestions.return_value = [
            {"command": "main.py diff-summary", "reason": "You have uncommitted changes."}
        ]

        _run_next_logic(self.project_dir, yes=False)

        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_subprocess_run.assert_not_called()

    @patch('shared.cli_utils.get_suggestions')
    @patch('subprocess.run')
    def test_next_command_no_suggestions(self, mock_subprocess_run, mock_get_suggestions):
        mock_get_suggestions.return_value = []

        _run_next_logic(self.project_dir, yes=False)

        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)
        mock_subprocess_run.assert_not_called()

    @patch('shared.cli_utils.get_suggestions')
    @patch('subprocess.run')
    def test_next_command_with_yes_flag(self, mock_subprocess_run, mock_get_suggestions):
        mock_get_suggestions.return_value = [
            {"command": "main.py test", "reason": "Tests have not been run."}
        ]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        _run_next_logic(self.project_dir, yes=True)

        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)
        expected_command = [sys.executable, str(self.main_py_path.resolve()), 'test']
        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.project_dir)

if __name__ == '__main__':
    unittest.main()