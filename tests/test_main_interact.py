import argparse
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

import main

class TestMainInteract(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up the directory if needed
        pass

    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('main.run_status')
    def test_interact_status(self, mock_run_status, mock_input):
        """Test that 'interact' command calls run_status on '1'."""
        args = argparse.Namespace(
            command='interact',
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)

        mock_run_status.assert_called_once_with(args)
        self.assertEqual(cm.exception.code, 0)

    @patch('builtins.input', side_effect=['3', 'q'])
    @patch('main._run_test_logic')
    def test_interact_test(self, mock_run_test_logic, mock_input):
        """Test that 'interact' command calls _run_test_logic on '3'."""
        args = argparse.Namespace(
            command='interact',
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)

        mock_run_test_logic.assert_called_once()
        self.assertEqual(cm.exception.code, 0)

    @patch('builtins.input', side_effect=['6', 'Test commit', 'q'])
    @patch('main._run_commit_logic')
    def test_interact_commit(self, mock_run_commit_logic, mock_input):
        """Test that 'interact' command calls _run_commit_logic on '6'."""
        args = argparse.Namespace(
            command='interact',
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)

        mock_run_commit_logic.assert_called_once()
        # Check that the commit logic was called with a namespace that includes the message
        call_args = mock_run_commit_logic.call_args[0][0]
        self.assertEqual(call_args.message, "Test commit")
        self.assertEqual(cm.exception.code, 0)

    @patch('builtins.input', side_effect=['invalid', 'q'])
    def test_interact_invalid_choice(self, mock_input):
        """Test that 'interact' command handles invalid input."""
        args = argparse.Namespace(
            command='interact',
            project_dir=self.project_dir
        )
        # We don't need to assert anything here, just that it runs without error
        with self.assertRaises(SystemExit) as cm:
            main.run_interact(args)
        self.assertEqual(cm.exception.code, 0)

if __name__ == '__main__':
    unittest.main()
