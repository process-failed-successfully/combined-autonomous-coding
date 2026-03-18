import argparse
import io
import sys
import unittest

from shared.base91_lab import base91_encode, base91_decode, run_base91_lab_logic


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

    def test_encode_hello_world(self):
        self.assertEqual(base91_encode(b"Hello World!"), ">OwJh>Io0Tv!8PE")

    def test_decode_hello_world(self):
        self.assertEqual(base91_decode(">OwJh>Io0Tv!8PE"), b"Hello World!")

    def test_encode_special_chars(self):
        self.assertEqual(base91_encode(b"\x00\x01\x02\x03"), ":C#(A")

    def test_decode_special_chars(self):
        self.assertEqual(base91_decode(":C#(A"), b"\x00\x01\x02\x03")

    def test_run_logic_encode(self):
        args = argparse.Namespace(encode="test", decode=None, tui=False)
        result = run_base91_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "fPNKd")

    def test_run_logic_decode(self):
        args = argparse.Namespace(encode=None, decode="fPNKd", tui=False)
        result = run_base91_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "test")

    def test_run_logic_no_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_base91_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("No action specified", self.held_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
