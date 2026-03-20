import unittest
from unittest.mock import patch
import io
import argparse

from shared.base45_lab import b45encode, b45decode, run_base45_lab_logic


class TestBase45Lab(unittest.TestCase):
    def test_encode_empty(self):
        self.assertEqual(b45encode(b""), "")

    def test_decode_empty(self):
        self.assertEqual(b45decode(""), b"")

    def test_encode_hello_world(self):
        self.assertEqual(b45encode(b"Hello!!"), "%69 VD92EX0")

    def test_encode_rfc_examples(self):
        self.assertEqual(b45encode(b"AB"), "BB8")
        self.assertEqual(b45encode(b"Hello!!"), "%69 VD92EX0")
        self.assertEqual(b45encode(b"base-45"), "UJCLQE7W581")

    def test_decode_hello_world(self):
        self.assertEqual(b45decode("%69 VD92EX0"), b"Hello!!")

    def test_decode_rfc_examples(self):
        self.assertEqual(b45decode("BB8"), b"AB")
        self.assertEqual(b45decode("UJCLQE7W581"), b"base-45")

    def test_decode_invalid_char(self):
        with self.assertRaises(ValueError):
            b45decode("BB8_")  # '_' is not in base45 alphabet

    def test_decode_invalid_length(self):
        with self.assertRaises(ValueError):
            # A valid base45 string cannot have length (3*n + 1)
            b45decode("A")

    def test_decode_invalid_sequence(self):
        with self.assertRaises(ValueError):
            # Invalid sequence resulting in value > 0xFFFF
            b45decode(":::")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_encode(self, mock_stdout):
        args = argparse.Namespace(encode="AB", decode=None, tui=False)
        success = run_base45_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "BB8")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_decode(self, mock_stdout):
        args = argparse.Namespace(encode=None, decode="BB8", tui=False)
        success = run_base45_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "AB")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        success = run_base45_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=":::", tui=False)
        success = run_base45_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error processing base45: Invalid Base45 sequence", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
