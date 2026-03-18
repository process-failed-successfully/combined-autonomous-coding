import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path

from main import run_base91_lab


class TestBase91TuiRun(unittest.TestCase):
    @patch("shared.tui.AgentTUI.run")
    def test_run_base91_lab_tui_sync(self, mock_run):
        """Test launching the TUI synchronously."""
        args = argparse.Namespace(tui=True, project_dir=Path("."))

        # We need to catch SystemExit since run_tui usually calls sys.exit(0)
        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit
            with self.assertRaises(SystemExit):
                run_base91_lab(args)

            mock_run.assert_called_once()

    @patch("shared.tui.AgentTUI.run_async")
    @patch("asyncio.get_running_loop")
    def test_run_base91_lab_tui_async(self, mock_get_loop, mock_run_async):
        """Test launching the TUI when an event loop is already running."""
        args = argparse.Namespace(tui=True, project_dir=Path("."))

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True
        mock_get_loop.return_value = mock_loop

        with patch("sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit
            with self.assertRaises(SystemExit):
                run_base91_lab(args)

            mock_run_async.assert_called_once()
