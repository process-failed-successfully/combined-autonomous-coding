import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import argparse
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

# Ensure the main script can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main

class TestNextCommand(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a mock parser and arguments for each test."""
        self.parser = main.get_parser()

    @patch('main.get_suggestions')
    async def test_next_no_suggestion(self, mock_get_suggestions):
        """Test the 'next' command when there are no suggestions."""
        mock_get_suggestions.return_value = []

        args = self.parser.parse_args(['next'])

        with self.assertRaises(SystemExit) as cm, redirect_stdout(io.StringIO()) as f:
            await main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        output = f.getvalue()
        self.assertIn("Project is in a clean state", output)

    @patch('builtins.input', return_value='y')
    @patch('main.get_suggestions')
    async def test_next_simple_suggestion_with_confirmation(self, mock_get_suggestions, mock_input):
        """Test 'next' with a simple suggestion and user confirmation."""
        mock_get_suggestions.return_value = [{
            'command': './main.py status',
            'reason': 'To check the project status.'
        }]

        args = self.parser.parse_args(['next'])

        # Mock the synchronous function
        mock_run_status = MagicMock(side_effect=SystemExit(0))

        with patch.dict(main.COMMAND_MAP, {'status': mock_run_status}):
            with self.assertRaises(SystemExit) as cm:
                await main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_status.assert_called_once()
        called_args = mock_run_status.call_args[0][0]
        self.assertEqual(called_args.command, 'status')

    @patch('builtins.input', return_value='n')
    @patch('main.get_suggestions')
    async def test_next_suggestion_with_rejection(self, mock_get_suggestions, mock_input):
        """Test 'next' when the user rejects the suggestion."""
        mock_get_suggestions.return_value = [{
            'command': './main.py status',
            'reason': 'To check the project status.'
        }]

        args = self.parser.parse_args(['next'])
        mock_run_status = MagicMock()

        with patch.dict(main.COMMAND_MAP, {'status': mock_run_status}):
            with self.assertRaises(SystemExit) as cm, redirect_stdout(io.StringIO()) as f:
                await main.run_next(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Aborted.", f.getvalue())
        mock_run_status.assert_not_called()

    @patch('main.get_suggestions')
    async def test_next_with_yes_flag(self, mock_get_suggestions):
        """Test 'next' with the --yes flag, skipping user confirmation."""
        mock_get_suggestions.return_value = [{
            'command': './main.py commit -m "Initial commit"',
            'reason': 'To commit staged changes.'
        }]

        args = self.parser.parse_args(['next', '--yes'])
        mock_run_commit = MagicMock(side_effect=SystemExit(0))

        with patch.dict(main.COMMAND_MAP, {'commit': mock_run_commit}):
            with self.assertRaises(SystemExit):
                await main.run_next(args)

        mock_run_commit.assert_called_once()
        called_args = mock_run_commit.call_args[0][0]
        self.assertEqual(called_args.command, 'commit')
        self.assertEqual(called_args.message, 'Initial commit')

    @patch('builtins.input', return_value='y')
    @patch('main.get_suggestions')
    async def test_next_with_command_arguments(self, mock_get_suggestions, mock_input):
        """Test 'next' with a command that includes arguments."""
        mock_get_suggestions.return_value = [{
            'command': './main.py commit --message "feat: A new feature"',
            'reason': 'To commit changes.'
        }]

        args = self.parser.parse_args(['next'])
        mock_run_commit = MagicMock(side_effect=SystemExit(0))

        with patch.dict(main.COMMAND_MAP, {'commit': mock_run_commit}):
            with self.assertRaises(SystemExit):
                await main.run_next(args)

        mock_run_commit.assert_called_once()
        called_args = mock_run_commit.call_args[0][0]
        self.assertEqual(called_args.command, 'commit')
        self.assertEqual(called_args.message, 'feat: A new feature')
        self.assertFalse(called_args.run_tests)

    @patch('main.get_suggestions')
    async def test_next_with_unexecutable_suggestion(self, mock_get_suggestions):
        """Test 'next' when the suggested command is not a valid subcommand."""
        mock_get_suggestions.return_value = [{
            'command': './main.py non_existent_command',
            'reason': 'A bad suggestion.'
        }]

        args = self.parser.parse_args(['next', '--yes'])

        with self.assertRaises(SystemExit) as cm, redirect_stderr(io.StringIO()) as f:
            await main.run_next(args)

        self.assertEqual(cm.exception.code, 2)  # Argparse exits with 2 for invalid choice
        self.assertIn("invalid choice: 'non_existent_command'", f.getvalue())

    @patch('builtins.input', return_value='y')
    @patch('main.get_suggestions')
    async def test_next_handles_async_functions(self, mock_get_suggestions, mock_input):
        """Test 'next' correctly handles calling async functions like run_plan."""
        mock_get_suggestions.return_value = [{
            'command': './main.py plan --spec app_spec.txt',
            'reason': 'To generate a plan.'
        }]

        args = self.parser.parse_args(['next'])

        spec_file = Path('app_spec.txt')
        spec_file.touch()

        # Use AsyncMock for the async function
        mock_run_plan = AsyncMock(side_effect=SystemExit(0))

        with patch.dict(main.COMMAND_MAP, {'plan': mock_run_plan}):
            with self.assertRaises(SystemExit):
                await main.run_next(args)

        spec_file.unlink()
        mock_run_plan.assert_awaited_once()
        called_args = mock_run_plan.call_args[0][0]
        self.assertEqual(called_args.command, 'plan')
        self.assertEqual(called_args.spec, Path('app_spec.txt'))

if __name__ == '__main__':
    unittest.main()
