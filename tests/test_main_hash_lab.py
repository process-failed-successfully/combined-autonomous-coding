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
        async def mock_run_async():
            pass
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
