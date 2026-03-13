import unittest
from unittest.mock import patch
import io
import argparse

from shared.base58_lab import b58encode, b58decode, run_base58_lab_logic


class TestBase58Lab(unittest.TestCase):
    def test_encode_empty(self):
        self.assertEqual(b58encode(b""), "")

    def test_decode_empty(self):
        self.assertEqual(b58decode(""), b"")

    def test_encode_hello_world(self):
        self.assertEqual(b58encode(b"Hello World"), "JxF12TrwUP45BMd")

    def test_decode_hello_world(self):
        self.assertEqual(b58decode("JxF12TrwUP45BMd"), b"Hello World")

    def test_encode_leading_zeros(self):
        self.assertEqual(b58encode(b"\x00\x00\x00ab"), "1118Qq")

    def test_decode_leading_zeros(self):
        self.assertEqual(b58decode("1118Qq"), b"\x00\x00\x00ab")

    def test_decode_invalid_char(self):
        with self.assertRaises(ValueError):
            b58decode("0OIl")  # These characters are not in base58 alphabet

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_encode(self, mock_stdout):
        args = argparse.Namespace(encode="Hello World", decode=None, tui=False)
        success = run_base58_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "JxF12TrwUP45BMd")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_decode(self, mock_stdout):
        args = argparse.Namespace(encode=None, decode="JxF12TrwUP45BMd", tui=False)
        success = run_base58_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "Hello World")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        success = run_base58_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode="0OIl", tui=False)
        success = run_base58_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error processing base58: Invalid character", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
