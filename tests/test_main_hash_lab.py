import unittest
from unittest.mock import patch, MagicMock
import sys

from main import parse_args, run_hash_lab
from pathlib import Path

class TestMainHashLab(unittest.TestCase):
    @patch('shared.tui.AgentTUI')
    @patch('main.sys.exit')
    def test_hash_lab_tui_command(self, mock_exit, mock_agent_tui):
        # Mock the app instance
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app

        # Provide a mock run_async method to handle asyncio execution if present
        mock_run_async = MagicMock()
        mock_app.run_async = mock_run_async

        # Parse args for hash-lab tui
        args = parse_args(['--project-dir', '.', 'hash-lab', 'tui'])

        # Verify the parsed action is correct
        self.assertEqual(args.command, 'hash-lab')
        self.assertEqual(args.action, 'tui')

        # Prevent sys.exit from actually exiting the test runner
        mock_exit.side_effect = SystemExit(0)

        # Run the command
        with self.assertRaises(SystemExit) as context:
            run_hash_lab(args)

        # Verify sys.exit was called with 0
        self.assertEqual(context.exception.code, 0)

        # Assert AgentTUI was created with the correct start_tab
        mock_agent_tui.assert_called_once_with(
            project_dir=Path('.'),
            start_tab='tab-hash'
        )

        # Assert app.run_async or app.run was called
        # Depending on how the mocked app.run_async behaves, the async call happens
        # It's sufficient to know that the AgentTUI was instantiated and sys.exit(0) was triggered.
        # Verify app.run was called since there is no running loop in this sync test
        mock_app.run.assert_called_once()

    @patch('shared.tui.AgentTUI')
    @patch('main.sys.exit')
    @patch('main.asyncio.ensure_future')
    def test_hash_lab_tui_command_async_loop(self, mock_ensure_future, mock_exit, mock_agent_tui):
        # Mock the app instance
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app

        # Provide a mock run_async method to handle asyncio execution if present
        mock_run_async = MagicMock()
        mock_app.run_async = mock_run_async

        # Parse args for hash-lab tui
        args = parse_args(['--project-dir', '.', 'hash-lab', 'tui'])

        # Prevent sys.exit from actually exiting the test runner
        mock_exit.side_effect = SystemExit(0)

        # We will run this in a real asyncio event loop so asyncio.get_running_loop() succeeds
        import asyncio
        async def run_in_loop():
            # In async loop, sys.exit(0) is skipped so there's no SystemExit raised
            run_hash_lab(args)

        asyncio.run(run_in_loop())

        # Assert AgentTUI was created with the correct start_tab
        mock_agent_tui.assert_called_once_with(
            project_dir=Path('.'),
            start_tab='tab-hash'
        )

        # Ensure asyncio.ensure_future was called since loop was running
        mock_ensure_future.assert_called_once()
        mock_app.run.assert_not_called()

    @patch('main.run_hash_lab_logic')
    @patch('main.sys.exit')
    def test_hash_lab_string_command(self, mock_exit, mock_logic):
        mock_logic.return_value = True

        args = parse_args(['hash-lab', 'string', 'mytext'])

        self.assertEqual(args.command, 'hash-lab')
        self.assertEqual(args.action, 'string')

        mock_exit.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit) as context:
            run_hash_lab(args)

        self.assertEqual(context.exception.code, 0)
        mock_logic.assert_called_once_with(args)

if __name__ == '__main__':
    unittest.main()
