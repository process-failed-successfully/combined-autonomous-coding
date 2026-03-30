import unittest
from unittest.mock import patch
import io
import argparse

from shared.binary_lab import text_to_binary, binary_to_text, run_binary_lab_logic

class TestBinaryLab(unittest.TestCase):

    def test_encode_empty(self):
        self.assertEqual(text_to_binary(""), "")

    def test_decode_empty(self):
        self.assertEqual(binary_to_text(""), "")
        self.assertEqual(binary_to_text("   "), "")

    def test_encode_hello(self):
        # H=72=01001000, e=101=01100101, l=108=01101100, l=108=01101100, o=111=01101111
        expected = "01001000 01100101 01101100 01101100 01101111"
        self.assertEqual(text_to_binary("Hello"), expected)

    def test_decode_hello(self):
        binary_str = "01001000 01100101 01101100 01101100 01101111"
        self.assertEqual(binary_to_text(binary_str), "Hello")

    def test_decode_invalid_sequence(self):
        with self.assertRaises(ValueError) as context:
            binary_to_text("01001000 01100121")
        self.assertTrue("Invalid binary sequence" in str(context.exception))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_encode(self, mock_stdout):
        args = argparse.Namespace(encode="AB", decode=None, tui=False)
        success = run_binary_lab_logic(args)
        self.assertTrue(success)
        # A=65=01000001, B=66=01000010
        self.assertEqual(mock_stdout.getvalue().strip(), "01000001 01000010")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_decode(self, mock_stdout):
        args = argparse.Namespace(encode=None, decode="01000001 01000010", tui=False)
        success = run_binary_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "AB")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        success = run_binary_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode="010A0001", tui=False)
        success = run_binary_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error processing binary", mock_stderr.getvalue())
