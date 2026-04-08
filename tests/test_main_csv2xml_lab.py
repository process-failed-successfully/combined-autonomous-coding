import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import sys

from main import main

class TestMainCsv2XmlLab(unittest.TestCase):

    @patch("main.parse_args")
    @patch("shared.csv2xml_lab.run_csv2xml_lab_logic", return_value=True)
    def test_run_csv2xml_lab_logic(self, mock_logic, mock_parse_args):
        args = Namespace(command="csv2xml-lab", action=None, input="test.csv", project_dir=".", tui=False)
        mock_parse_args.return_value = args
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            try:
                import asyncio
                asyncio.run(main())
            except SystemExit:
                pass
            mock_logic.assert_called_once_with(args)
            mock_exit.assert_called_once_with(0)

    @patch("main.parse_args")
    @patch("shared.tui.AgentTUI")
    def test_run_csv2xml_lab_tui(self, mock_tui, mock_parse_args):
        args = Namespace(command="csv2xml-lab", action="tui", project_dir=".", tui=True)
        mock_parse_args.return_value = args
        mock_app_instance = MagicMock()
        mock_tui.return_value = mock_app_instance

        with patch('sys.exit', side_effect=SystemExit) as mock_exit, \
             patch('asyncio.get_running_loop') as mock_get_loop:

            # Simulate no running loop
            mock_get_loop.side_effect = RuntimeError("no loop")

            try:
                import asyncio
                asyncio.run(main())
            except SystemExit:
                pass

            mock_tui.assert_called_once()
            mock_app_instance.run.assert_called_once()
            mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    unittest.main()
