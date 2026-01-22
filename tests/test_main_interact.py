import unittest
from unittest.mock import patch
import argparse
from pathlib import Path

# Assuming main.py is in the parent directory or PYTHONPATH is set correctly
import main


class TestInteractCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch('builtins.input', side_effect=['1', 'q'])
    @patch('main.run_status')
    def test_interact_chooses_status(self, mock_run_status, mock_input):
        """Test that selecting '1' calls run_status."""
        args = argparse.Namespace(project_dir=self.project_dir)
        try:
            main.run_interact(args)
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        self.assertEqual(mock_input.call_count, 2)
        mock_run_status.assert_called_once()
        # Check that the argument passed to run_status is a Namespace with the correct project_dir
        called_args = mock_run_status.call_args[0][0]
        self.assertIsInstance(called_args, argparse.Namespace)
        self.assertEqual(called_args.project_dir, self.project_dir)

    @patch('builtins.input', side_effect=['2', 'q'])
    @patch('main.run_test')
    def test_interact_chooses_test(self, mock_run_test, mock_input):
        """Test that selecting '2' calls run_test."""
        args = argparse.Namespace(project_dir=self.project_dir)
        try:
            main.run_interact(args)
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        mock_run_test.assert_called_once()
        called_args = mock_run_test.call_args[0][0]
        self.assertEqual(called_args.project_dir, self.project_dir)
        self.assertEqual(called_args.test_args, [])

    @patch('builtins.input', side_effect=['5', 'Test commit message', 'q'])
    @patch('main.run_commit')
    def test_interact_chooses_commit(self, mock_run_commit, mock_input):
        """Test that selecting '5' prompts for a message and calls run_commit."""
        args = argparse.Namespace(project_dir=self.project_dir)
        try:
            main.run_interact(args)
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        self.assertEqual(mock_input.call_count, 3)
        mock_run_commit.assert_called_once()
        called_args = mock_run_commit.call_args[0][0]
        self.assertEqual(called_args.project_dir, self.project_dir)
        self.assertEqual(called_args.message, "Test commit message")
        self.assertFalse(called_args.run_tests)

    @patch('builtins.input', side_effect=['q'])
    def test_interact_quits(self, mock_input):
        """Test that 'q' exits the loop."""
        args = argparse.Namespace(project_dir=self.project_dir)
        try:
            main.run_interact(args)
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        # Should only be called once for the 'q'
        self.assertEqual(mock_input.call_count, 1)

    @patch('builtins.input', side_effect=['9', 'q'])  # Invalid choice, then quit
    @patch('main.run_status')
    @patch('main.run_test')
    @patch('main.run_commit')
    def test_interact_invalid_choice(self, mock_run_commit, mock_run_test, mock_run_status, mock_input):
        """Test that an invalid choice does not call any function."""
        args = argparse.Namespace(project_dir=self.project_dir)
        try:
            main.run_interact(args)
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        self.assertEqual(mock_input.call_count, 2)
        mock_run_status.assert_not_called()
        mock_run_test.assert_not_called()
        mock_run_commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
