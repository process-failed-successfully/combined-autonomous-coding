import unittest
import argparse
from unittest.mock import patch
from shared.base64_lab import run_base64_lab_logic

class TestBase64Lab(unittest.TestCase):
    @patch('builtins.print')
    def test_encode(self, mock_print):
        args = argparse.Namespace(encode="hello", decode=None)
        success = run_base64_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called_with("aGVsbG8=")

    @patch('builtins.print')
    def test_decode(self, mock_print):
        args = argparse.Namespace(encode=None, decode="aGVsbG8=")
        success = run_base64_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called_with("hello")

    @patch('sys.stderr.write')
    def test_missing_args(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode=None)
        success = run_base64_lab_logic(args)
        self.assertFalse(success)

    @patch('sys.stderr.write')
    def test_invalid_decode(self, mock_stderr):
        args = argparse.Namespace(encode=None, decode="invalidbase64!@#")
        success = run_base64_lab_logic(args)
        self.assertFalse(success)
