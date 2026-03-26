import argparse
import io
import sys
import unittest
from unittest.mock import patch, MagicMock

from shared.octal_lab import octal_encode, octal_decode, run_octal_lab_logic
from main import run_octal_lab


class TestOctalLab(unittest.TestCase):
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

    def test_encode_hello(self):
        data = b"hello"
        encoded = octal_encode(data)
        self.assertEqual(encoded, "150 145 154 154 157")

    def test_decode_hello(self):
        decoded = octal_decode("150 145 154 154 157")
        self.assertEqual(decoded, b"hello")

    def test_decode_invalid(self):
        with self.assertRaises(ValueError):
            octal_decode("invalid string")

    def test_encode_empty(self):
        self.assertEqual(octal_encode(b""), "")

    def test_decode_empty(self):
        self.assertEqual(octal_decode(""), b"")

    def test_logic_encode(self):
        args = argparse.Namespace(encode="hello", decode=None, tui=False)
        result = run_octal_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "150 145 154 154 157")

    def test_logic_decode(self):
        args = argparse.Namespace(encode=None, decode="150 145 154 154 157", tui=False)
        result = run_octal_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "hello")

    def test_logic_no_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_octal_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", self.held_stderr.getvalue())

    def test_logic_invalid_decode(self):
        args = argparse.Namespace(encode=None, decode="INVALID", tui=False)
        result = run_octal_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error processing octal", self.held_stderr.getvalue())

    @patch('main.sys.exit')
    @patch('shared.tui.AgentTUI')
    def test_run_octal_lab_tui(self, mock_agent_tui, mock_exit):
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        mock_exit.side_effect = SystemExit
        args = argparse.Namespace(command="octal-lab", tui=True, project_dir=None)

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_octal_lab(args)
            except SystemExit:
                pass

        mock_agent_tui.assert_called_once_with(project_dir=None, start_tab="tab-octal")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.sys.exit')
    @patch('shared.octal_lab.run_octal_lab_logic')
    def test_run_octal_lab_cli(self, mock_logic, mock_exit):
        mock_logic.return_value = True
        args = argparse.Namespace(command="octal-lab", tui=False, encode="test")

        with patch.dict('sys.modules', {'shared.octal_lab': MagicMock(run_octal_lab_logic=mock_logic)}):
            run_octal_lab(args)

        mock_logic.assert_called_once_with(args)
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
