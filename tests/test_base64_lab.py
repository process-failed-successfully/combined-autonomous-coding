import unittest
import argparse
from unittest.mock import patch
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

    @patch('shared.tui.AgentTUI.run')
    @patch('shared.tui.AgentTUI.__init__', return_value=None)
    def test_tui_launch(self, mock_tui_init, mock_tui_run):
        from main import run_base64_lab
        args = argparse.Namespace(command="base64-lab", encode=None, decode=None, tui=True, project_dir=".")

        with patch('sys.exit') as mock_exit:
            # We must simulate exit by raising a custom exception or just mock it to raise SystemExit
            mock_exit.side_effect = SystemExit(0)
            try:
                run_base64_lab(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)
            mock_exit.assert_called_with(0)

        mock_tui_init.assert_called_with(project_dir=".", start_tab="tab-base64")
        mock_tui_run.assert_called_once()

    @patch('sys.stderr.write')
    def test_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode="invalidbase64!@#")
        success = run_base64_lab_logic(args)
        self.assertFalse(success)
