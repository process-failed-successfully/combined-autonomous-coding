import argparse
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure main is importable
sys.path.append(str(Path(__file__).parent.parent))

from main import run_stats_lab  # noqa: E402


class TestCliTuiEventLoop(unittest.IsolatedAsyncioTestCase):
    @patch('main.sys.exit')
    @patch('shared.tui.AgentTUI')
    async def test_run_tui_with_running_loop(self, mock_agent_tui, mock_exit):
        """
        Test that when an async loop is already running, triggering a TUI
        calls run_async() via asyncio.ensure_future rather than throwing
        RuntimeError from app.run().
        """
        mock_app = MagicMock()

        # Mock run_async to return a dummy coroutine
        async def dummy_coro():
            pass

        mock_app.run_async.return_value = dummy_coro()
        mock_agent_tui.return_value = mock_app

        args = argparse.Namespace(
            project_dir=Path('.'),
            action='tui',
            format='text'
        )

        # Call the synchronous function that creates the TUI.
        # Because we are inside IsolatedAsyncioTestCase, there IS a running loop.
        # Ensure it doesn't sys.exit before the assert
        mock_exit.side_effect = SystemExit

        try:
            run_stats_lab(args)
        except SystemExit:
            pass

        # Verify that app.run() was NOT called
        mock_app.run.assert_not_called()

        # Verify that run_async() WAS called
        mock_app.run_async.assert_called_once()

        # Verify sys.exit(0) was called
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
