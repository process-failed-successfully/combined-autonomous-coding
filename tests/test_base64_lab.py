import unittest
import argparse
from unittest.mock import patch, MagicMock
from shared.base64_lab import run_base64_lab_logic

class TestBase64Lab(unittest.TestCase):
    @patch('builtins.print')
    def test_encode(self, mock_print):
        args = argparse.Namespace(encode="hello", decode=None)
        success = run_base64_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called_with("aGVsbG8=")

    @patch('builtins.print')
    def test_decode(self, mock_print):
        args = argparse.Namespace(encode=None, decode="aGVsbG8=")
        success = run_base64_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called_with("hello")

    @patch('sys.stderr.write')
    def test_missing_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None)
        success = run_base64_lab_logic(args)
        self.assertFalse(success)

    from unittest.mock import MagicMock
    @patch('main.sys.exit')
    def test_tui_launch(self, mock_exit):
        mock_agent_tui = MagicMock()
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        # Mock sys.exit to raise an exception so we don't fall through to the logic block
        mock_exit.side_effect = SystemExit(0)
        from main import run_base64_lab
        args = argparse.Namespace(command="base64-lab", encode=None, decode=None, tui=True, project_dir=".", _in_event_loop=False)

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_base64_lab(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        mock_agent_tui.assert_called_with(project_dir=".", start_tab="tab-base64")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_with(0)

    @patch('sys.stderr.write')
    def test_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode="invalidbase64!@#")
        success = run_base64_lab_logic(args)
        self.assertFalse(success)
