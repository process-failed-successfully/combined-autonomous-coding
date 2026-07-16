import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import sys

from main import run_semver_lab

class TestMainSemverLab(unittest.TestCase):

    @patch("shared.semver_lab.run_semver_lab_logic")
    def test_run_semver_lab_logic(self, mock_logic):
        args = Namespace(command="semver-lab", action="parse", version="1.0.0", project_dir=".")
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            try:
                run_semver_lab(args)
            except SystemExit:
                pass
            mock_logic.assert_called_once_with(args)
            mock_exit.assert_called_once_with(0)

    @patch.dict("sys.modules", {"shared.tui": MagicMock(AgentTUI=MagicMock())})
    def test_run_semver_lab_tui(self):
        mock_tui_module = sys.modules["shared.tui"]
        mock_tui = mock_tui_module.AgentTUI
        args = Namespace(command="semver-lab", action="tui", project_dir=".")
        mock_app_instance = MagicMock()
        mock_tui.return_value = mock_app_instance

        with patch('sys.exit', side_effect=SystemExit) as mock_exit, \
             patch('asyncio.get_running_loop') as mock_get_loop, \
             patch('main.run_tui') as mock_run_tui:

            # Simulate no running loop
            mock_get_loop.side_effect = RuntimeError("no loop")

            try:
                run_semver_lab(args)
            except SystemExit:
                pass

            mock_run_tui.assert_called_once_with(args, start_tab="tab-semver")

if __name__ == "__main__":
    unittest.main()
