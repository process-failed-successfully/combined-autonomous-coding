import unittest
from unittest.mock import patch
import io
import argparse

from shared.base62_lab import b62encode, b62decode, run_base62_lab_logic


class TestBase62Lab(unittest.TestCase):
    def test_encode_empty(self):
        self.assertEqual(b62encode(b""), "")

    def test_decode_empty(self):
        self.assertEqual(b62decode(""), b"")

    def test_encode_hello_world(self):
        self.assertEqual(b62encode(b"Hello World"), "73XpUgyMwkGr29M")

    def test_decode_hello_world(self):
        self.assertEqual(b62decode("73XpUgyMwkGr29M"), b"Hello World")

    def test_encode_leading_zeros(self):
        self.assertEqual(b62encode(b"\x00\x00\x00ab"), "0006U6")

    def test_decode_leading_zeros(self):
        self.assertEqual(b62decode("0006U6"), b"\x00\x00\x00ab")

    def test_decode_invalid_char(self):
        with self.assertRaises(ValueError):
            b62decode("0OIl_")  # '_' is not in base62 alphabet

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_encode(self, mock_stdout):
        args = argparse.Namespace(encode="Hello World", decode=None, tui=False)
        success = run_base62_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "73XpUgyMwkGr29M")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_decode(self, mock_stdout):
        args = argparse.Namespace(encode=None, decode="73XpUgyMwkGr29M", tui=False)
        success = run_base62_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "Hello World")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        success = run_base62_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode="0OIl_", tui=False)
        success = run_base62_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error processing base62: Invalid character", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
