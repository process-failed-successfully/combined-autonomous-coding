import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace

from main import run_xml_lab


class TestMainXmlLab(unittest.TestCase):

    @patch("shared.xml_lab.run_xml_lab_logic")
    def test_run_xml_lab_logic(self, mock_logic):
        args = Namespace(command="xml-lab", action="format", input="test.xml", project_dir=".")
        with patch('sys.exit', side_effect=SystemExit) as mock_exit:
            try:
                run_xml_lab(args)
            except SystemExit:
                pass
            mock_logic.assert_called_once_with(args)
            mock_exit.assert_called_once_with(0)

    @patch("shared.tui.AgentTUI")
    def test_run_xml_lab_tui(self, mock_tui):
        args = Namespace(command="xml-lab", action="tui", project_dir=".")
        mock_app_instance = MagicMock()
        mock_tui.return_value = mock_app_instance

        with patch('sys.exit', side_effect=SystemExit) as mock_exit, \
             patch('asyncio.get_running_loop') as mock_get_loop:

            # Simulate no running loop
            mock_get_loop.side_effect = RuntimeError("no loop")

            try:
                run_xml_lab(args)
            except SystemExit:
                pass

            mock_tui.assert_called_once_with(project_dir=".", start_tab="tab-xml")
            mock_app_instance.run.assert_called_once()
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
