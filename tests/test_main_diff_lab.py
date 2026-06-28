import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import asyncio

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import parse_args, main
import argparse

class TestMainDiffLab(unittest.IsolatedAsyncioTestCase):

    @patch('main.run_diff_lab_logic')
    async def test_diff_lab_cli_without_files(self, mock_run_logic):
        # Setup sys.argv
        test_args = ["main.py", "diff-lab"]
        with patch.object(sys, 'argv', test_args):
            with patch('builtins.print') as mock_print:
                with self.assertRaises(SystemExit) as cm:
                    await main()
                self.assertEqual(cm.exception.code, 1)
                mock_print.assert_any_call("Error: file1 and file2 are required unless --tui is specified.", file=sys.stderr)
                mock_run_logic.assert_not_called()

    @patch('main.run_diff_lab_logic')
    async def test_diff_lab_cli_with_files(self, mock_run_logic):
        # run_diff_lab_logic calls sys.exit(0)
        mock_run_logic.side_effect = SystemExit(0)
        # Setup sys.argv
        test_args = ["main.py", "diff-lab", "file1.txt", "file2.txt"]
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                await main()
            self.assertEqual(cm.exception.code, 0)
        mock_run_logic.assert_called_once()
        args = mock_run_logic.call_args[0][0]
        self.assertEqual(args.file1, "file1.txt")
        self.assertEqual(args.file2, "file2.txt")
        self.assertFalse(getattr(args, 'tui', False))

    @patch('shared.tui.AgentTUI')
    async def test_diff_lab_cli_with_tui(self, mock_agent_tui):
        test_args = ["main.py", "diff-lab", "--tui"]
        # Make the mock instance return something that behaves like an awaitable
        mock_app_instance = mock_agent_tui.return_value

        async def mock_run_async():
            pass

        mock_app_instance.run_async.side_effect = mock_run_async

        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                await main()
            self.assertEqual(cm.exception.code, 0)
            mock_agent_tui.assert_called_once()
            call_kwargs = mock_agent_tui.call_args[1]
            self.assertEqual(call_kwargs.get("start_tab"), "tab-diff")

if __name__ == '__main__':
    unittest.main()
