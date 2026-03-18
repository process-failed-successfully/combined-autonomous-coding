import argparse
import io
import sys
import unittest
from unittest.mock import patch, MagicMock

from shared.base91_lab import base91_encode, base91_decode, run_base91_lab_logic
from main import run_base91_lab


class TestBase91Lab(unittest.TestCase):
    def setUp(self):
        self.held_stdout = io.StringIO()
        self.held_stderr = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def test_encode_empty(self):
        self.assertEqual(base91_encode(b""), "")

    def test_decode_empty(self):
        self.assertEqual(base91_decode(""), b"")

    def test_encode_logic(self):
        args = argparse.Namespace(encode="Hello World!", decode=None, tui=False)
        result = run_base91_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), ">OwJh>Io0Tv!8PE")

    def test_decode_logic(self):
        args = argparse.Namespace(encode=None, decode=">OwJh>Io0Tv!8PE", tui=False)
        result = run_base91_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "Hello World!")

    def test_no_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_base91_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", self.held_stderr.getvalue())

    def test_invalid_decode(self):
        # Decoding "~~~" results in invalid UTF-8 bytes.
        # run_base91_lab_logic tries to `.decode('utf-8')` the result, which will fail.
        # It catches the exception and returns False.
        args = argparse.Namespace(encode=None, decode="~~~", tui=False)
        result = run_base91_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error processing base91", self.held_stderr.getvalue())

    @patch('main.sys.exit')
    @patch('shared.tui.AgentTUI')
    def test_run_base91_lab_tui(self, mock_agent_tui, mock_exit):
        # We need to test the local import patch
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        args = argparse.Namespace(command="base91-lab", tui=True, project_dir=None, _in_event_loop=False)

        mock_exit.side_effect = SystemExit

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_base91_lab(args)
            except SystemExit:
                pass

        mock_agent_tui.assert_called_once_with(project_dir=None, start_tab="tab-base91")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.sys.exit')
    @patch('shared.base91_lab.run_base91_lab_logic')
    def test_run_base91_lab_cli(self, mock_logic, mock_exit):
        mock_logic.return_value = True
        args = argparse.Namespace(command="base91-lab", tui=False, encode="test")

        with patch.dict('sys.modules', {'shared.base91_lab': MagicMock(run_base91_lab_logic=mock_logic)}):
            run_base91_lab(args)

        mock_logic.assert_called_once_with(args)
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
