import unittest
from unittest.mock import patch, call
from pathlib import Path
import argparse
import io

# Make sure main.py is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_interact

class TestMainInteract(unittest.TestCase):

    @patch('main.run_suggest')
    @patch('main.run_commit')
    @patch('main.run_format')
    @patch('main.run_lint')
    @patch('main.run_test')
    @patch('main.run_status')
    @patch('builtins.input', side_effect=['1', '2', '3', '4', '5', 'some message', '6', 'q'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_interact_menu_calls(self, mock_stdout, mock_input, mock_run_status, mock_run_test, mock_run_lint, mock_run_format, mock_run_commit, mock_run_suggest):
        """
        Tests that selecting each menu item calls the correct underlying function.
        """
        # The side_effect for input will select '1', then '2', etc., and finally 'q' to quit.
        # For the commit command '5', it also provides a commit message.

        args = argparse.Namespace(project_dir=Path('.'))

        with self.assertRaises(SystemExit) as cm:
            run_interact(args)

        self.assertEqual(cm.exception.code, 0)

        # The interact function resolves the path, so we must assert against the resolved path.
        resolved_path = Path('.').resolve()

        # Verify that each function was called once with the correct arguments
        mock_run_status.assert_called_once_with(unittest.mock.ANY)
        self.assertEqual(mock_run_status.call_args[0][0].project_dir, resolved_path)

        mock_run_test.assert_called_once_with(unittest.mock.ANY)
        self.assertEqual(mock_run_test.call_args[0][0].project_dir, resolved_path)

        mock_run_lint.assert_called_once_with(unittest.mock.ANY)
        self.assertEqual(mock_run_lint.call_args[0][0].project_dir, resolved_path)
        self.assertFalse(mock_run_lint.call_args[0][0].fix)

        mock_run_format.assert_called_once_with(unittest.mock.ANY)
        self.assertEqual(mock_run_format.call_args[0][0].project_dir, resolved_path)
        self.assertFalse(mock_run_format.call_args[0][0].check)

        mock_run_commit.assert_called_once_with(unittest.mock.ANY)
        self.assertEqual(mock_run_commit.call_args[0][0].project_dir, resolved_path)
        self.assertEqual(mock_run_commit.call_args[0][0].message, 'some message')

        mock_run_suggest.assert_called_once_with(unittest.mock.ANY)
        self.assertEqual(mock_run_suggest.call_args[0][0].project_dir, resolved_path)

    @patch('builtins.input', side_effect=['invalid', 'q'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_interact_invalid_input(self, mock_stdout, mock_input):
        """
        Tests that the menu handles invalid input and continues.
        """
        args = argparse.Namespace(project_dir=Path('.'))

        with self.assertRaises(SystemExit) as cm:
            run_interact(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Invalid choice, please try again.", output)

    @patch('builtins.input', side_effect=['5', '']) # Select commit, then provide empty message
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('main.run_commit')
    def test_interact_commit_empty_message(self, mock_run_commit, mock_stdout, mock_input):
        """
        Tests that the commit action handles an empty message gracefully.
        """
        # The user quits implicitly after the empty message by not looping again
        # To make the test exit cleanly, we'll add 'q'
        mock_input.side_effect = ['5', '', 'q']

        args = argparse.Namespace(project_dir=Path('.'))

        with self.assertRaises(SystemExit) as cm:
            run_interact(args)

        self.assertEqual(cm.exception.code, 0)

        # run_commit should not have been called
        mock_run_commit.assert_not_called()

        output = mock_stdout.getvalue()
        self.assertIn("Commit message cannot be empty. Aborting.", output)

if __name__ == '__main__':
    unittest.main()
