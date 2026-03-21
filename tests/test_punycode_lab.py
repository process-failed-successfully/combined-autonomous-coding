import unittest
from unittest.mock import patch
import io
import argparse

from shared.punycode_lab import run_punycode_lab_logic


class TestPunycodeLab(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encode_valid_domain(self, mock_stdout):
        args = argparse.Namespace(encode="münchen.de", decode=None, tui=False)
        success = run_punycode_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "xn--mnchen-3ya.de")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_decode_valid_domain(self, mock_stdout):
        args = argparse.Namespace(encode=None, decode="xn--mnchen-3ya.de", tui=False)
        success = run_punycode_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "münchen.de")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_encode_invalid_domain(self, mock_stderr):
        # Using a very long label which violates IDNA max length
        long_label = "a" * 100 + ".com"
        args = argparse.Namespace(encode=long_label, decode=None, tui=False)
        success = run_punycode_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error processing punycode:", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        success = run_punycode_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
