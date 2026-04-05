import argparse
import io
import sys
import unittest
from unittest.mock import patch, MagicMock
from shared.base92_lab import run_base92_lab_logic, base92_encode, base92_decode
from main import run_base92_lab

class TestBase92Lab(unittest.TestCase):
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
        self.assertEqual(base92_encode(b""), "~")

    def test_decode_empty(self):
        self.assertEqual(base92_decode(""), b"")
        self.assertEqual(base92_decode("~"), b"")

    def test_encode_decode(self):
        test_strings = [
            b"hello world",
            b"test data 123 !@#",
            b"\x00\x01\x02\x03\xff\xfe\xfd",
            b"a" * 100
        ]
        for data in test_strings:
            encoded = base92_encode(data)
            decoded = base92_decode(encoded)
            self.assertEqual(decoded, data)

    def test_decode_invalid_char(self):
        with self.assertRaises(ValueError):
            base92_decode("\x00invalid")  # characters not in base92 dict

    def test_run_logic_encode(self):
        args = argparse.Namespace(encode="hello world", decode=None, tui=False)
        result = run_base92_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "Fc_$aOTdKnsM*k")

    def test_run_logic_decode(self):
        args = argparse.Namespace(encode=None, decode="Fc_$aOTdKnsM*k", tui=False)
        result = run_base92_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "hello world")

    def test_run_logic_no_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_base92_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", self.held_stderr.getvalue())

    def test_run_logic_invalid_decode(self):
        args = argparse.Namespace(encode=None, decode="\x00\x00!!!", tui=False)
        result = run_base92_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error processing base92:", self.held_stderr.getvalue())

    @patch('main.sys.exit')
    def test_run_base92_lab_tui(self, mock_exit):
        mock_agent_tui = MagicMock()
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        mock_exit.side_effect = SystemExit(0)
        args = argparse.Namespace(command="base92-lab", tui=True, project_dir=".", _in_event_loop=False)

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_base92_lab(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        mock_agent_tui.assert_called_once_with(project_dir=".", start_tab="tab-base92")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.sys.exit')
    @patch('shared.base92_lab.run_base92_lab_logic')
    def test_run_base92_lab_cli(self, mock_logic, mock_exit):
        mock_logic.return_value = True
        args = argparse.Namespace(command="base92", tui=False, encode="test")

        with patch.dict('sys.modules', {'shared.base92_lab': MagicMock(run_base92_lab_logic=mock_logic)}):
            run_base92_lab(args)

        mock_logic.assert_called_once_with(args)
        mock_exit.assert_called_once_with(0)

if __name__ == '__main__':
    unittest.main()
