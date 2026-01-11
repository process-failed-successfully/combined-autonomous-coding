import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import sys

from shared.commands import run_next

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch('shared.commands.get_suggestions')
    @patch('subprocess.run')
    @patch('builtins.input', return_value='y')
    def test_run_next_with_suggestion_and_confirmation(self, mock_input, mock_subprocess_run, mock_get_suggestions):
        mock_get_suggestions.return_value = [{'command': 'main.py test', 'reason': 'Run tests.'}]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once_with("\nExecute this command? [Y/n]: ")

        executable = sys.executable
        main_py_path = str(Path(__file__).parent.parent / "main.py")
        expected_command = [executable, main_py_path, 'test']

        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.project_dir)

    @patch('shared.commands.get_suggestions')
    @patch('subprocess.run')
    def test_run_next_with_yes_flag(self, mock_subprocess_run, mock_get_suggestions):
        mock_get_suggestions.return_value = [{'command': 'main.py commit -m "WIP"', 'reason': 'Commit changes.'}]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = argparse.Namespace(project_dir=self.project_dir, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)

        executable = sys.executable
        main_py_path = str(Path(__file__).parent.parent / "main.py")
        expected_command = [executable, main_py_path, 'commit', '-m', 'WIP']

        mock_subprocess_run.assert_called_once_with(expected_command, cwd=self.project_dir)

    @patch('shared.commands.get_suggestions')
    @patch('builtins.input', return_value='n')
    @patch('subprocess.run')
    def test_run_next_with_rejection(self, mock_subprocess_run, mock_input, mock_get_suggestions):
        mock_get_suggestions.return_value = [{'command': 'main.py test', 'reason': 'Run tests.'}]

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_not_called()

    @patch('shared.commands.get_suggestions')
    @patch('subprocess.run')
    def test_run_next_no_suggestions(self, mock_subprocess_run, mock_get_suggestions):
        mock_get_suggestions.return_value = []

        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
