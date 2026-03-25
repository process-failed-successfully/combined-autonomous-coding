import argparse
import io
import sys
import unittest
from unittest.mock import patch

from shared.octal_lab import run_octal_lab_logic


class TestOctalLab(unittest.TestCase):

    def test_encode(self):
        args = argparse.Namespace(encode="hello", decode=None, tui=False)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            success = run_octal_lab_logic(args)
            self.assertTrue(success)
            self.assertEqual(fake_out.getvalue().strip(), "150 145 154 154 157")

    def test_decode(self):
        args = argparse.Namespace(encode=None, decode="150 145 154 154 157", tui=False)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            success = run_octal_lab_logic(args)
            self.assertTrue(success)
            self.assertEqual(fake_out.getvalue().strip(), "hello")

    def test_decode_invalid(self):
        args = argparse.Namespace(encode=None, decode="150 xyz 154", tui=False)
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            success = run_octal_lab_logic(args)
            self.assertFalse(success)
            self.assertIn("Error: Invalid octal string.", fake_err.getvalue())

    def test_decode_invalid_utf8(self):
        args = argparse.Namespace(encode=None, decode="377", tui=False)
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            success = run_octal_lab_logic(args)
            self.assertFalse(success)
            self.assertIn("Error: Decoded bytes are not valid UTF-8.", fake_err.getvalue())

    def test_missing_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        with patch('sys.stderr', new=io.StringIO()) as fake_err:
            success = run_octal_lab_logic(args)
            self.assertFalse(success)
            self.assertIn("Error: must provide either --encode, --decode, or --tui", fake_err.getvalue())

if __name__ == '__main__':
    unittest.main()
