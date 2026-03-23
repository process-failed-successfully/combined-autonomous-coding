import unittest
import argparse
import base64
from unittest.mock import patch
import io
from shared.brotli_lab import BrotliLabManager, run_brotli_lab_logic

class TestBrotliLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = BrotliLabManager()

    def test_compress_decompress_roundtrip(self):
        test_data = b"Hello, Brotli Compression!"
        compressed = self.manager.compress(test_data)
        self.assertNotEqual(compressed, test_data)

        decompressed = self.manager.decompress(compressed)
        self.assertEqual(decompressed, test_data)

    def test_compress_with_different_quality(self):
        test_data = b"Hello, Brotli Compression!" * 100
        comp_q1 = self.manager.compress(test_data, quality=1)
        comp_q11 = self.manager.compress(test_data, quality=11)
        # Higher quality usually yields smaller or equal size
        self.assertLessEqual(len(comp_q11), len(comp_q1))

class TestBrotliLabLogic(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_compress_hex(self, mock_stdout):
        args = argparse.Namespace(compress="test data", quality=11, base64=False, decompress=None)
        success = run_brotli_lab_logic(args)
        self.assertTrue(success)
        output = mock_stdout.getvalue().strip()
        self.assertTrue(len(output) > 0)

        # Test decompress
        args_decomp = argparse.Namespace(decompress=output, quality=11, base64=False, compress=None)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout2:
            success = run_brotli_lab_logic(args_decomp)
            self.assertTrue(success)
            self.assertEqual(mock_stdout2.getvalue().strip(), "test data")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_compress_base64(self, mock_stdout):
        args = argparse.Namespace(compress="base64 test", quality=11, base64=True, decompress=None)
        success = run_brotli_lab_logic(args)
        self.assertTrue(success)
        output = mock_stdout.getvalue().strip()

        # Test decompress
        args_decomp = argparse.Namespace(decompress=output, quality=11, base64=True, compress=None)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout2:
            success = run_brotli_lab_logic(args_decomp)
            self.assertTrue(success)
            self.assertEqual(mock_stdout2.getvalue().strip(), "base64 test")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_no_args(self, mock_stderr):
        args = argparse.Namespace(compress=None, decompress=None, quality=11, base64=False)
        success = run_brotli_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("must provide either", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
