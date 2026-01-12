import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys
from io import StringIO

from main import run_next

class TestMainNext(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch('shared.cli_utils.get_suggestions')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_next_no_suggestions(self, mock_stdout, mock_get_suggestions):
        mock_get_suggestions.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Project is in a clean state", output)

    @patch('subprocess.run')
    @patch('builtins.input', return_value='y')
    @patch('shared.cli_utils.get_suggestions')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_next_with_suggestion_and_approval(self, mock_stdout, mock_get_suggestions, mock_input, mock_subprocess_run):
        mock_get_suggestions.return_value = [{'command': 'main.py test', 'reason': 'Run tests to verify changes.'}]
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("--- Suggested Next Step ---", output)
        self.assertIn("Command: main.py test", output)

        mock_subprocess_run.assert_called_once()
        called_args = mock_subprocess_run.call_args[0][0]
        self.assertEqual(called_args[1], 'main.py')
        self.assertEqual(called_args[2], 'test')


    @patch('subprocess.run')
    @patch('builtins.input', return_value='n')
    @patch('shared.cli_utils.get_suggestions')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_next_with_suggestion_and_denial(self, mock_stdout, mock_get_suggestions, mock_input, mock_subprocess_run):
        mock_get_suggestions.return_value = [{'command': 'main.py commit -m "Initial commit"', 'reason': 'Commit your work.'}]
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()
        self.assertIn("Aborted.", output)
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
