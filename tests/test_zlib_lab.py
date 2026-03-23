import unittest
import argparse
from shared.zlib_lab import ZlibLabManager, run_zlib_lab_logic
import base64

from unittest.mock import patch
import io


class TestZlibLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ZlibLabManager()
        self.test_data = b"Hello, World! " * 50

    def test_compress_decompress_zlib(self):
        compressed = self.manager.compress(self.test_data, format="zlib")
        self.assertNotEqual(compressed, self.test_data)
        self.assertTrue(len(compressed) < len(self.test_data))
        decompressed = self.manager.decompress(compressed, format="zlib")
        self.assertEqual(decompressed, self.test_data)

    def test_compress_decompress_deflate(self):
        compressed = self.manager.compress(self.test_data, format="deflate")
        self.assertNotEqual(compressed, self.test_data)
        decompressed = self.manager.decompress(compressed, format="deflate")
        self.assertEqual(decompressed, self.test_data)

    def test_compress_decompress_gzip(self):
        compressed = self.manager.compress(self.test_data, format="gzip")
        self.assertTrue(compressed.startswith(b"\x1f\x8b"))
        decompressed = self.manager.decompress(compressed, format="gzip")
        self.assertEqual(decompressed, self.test_data)

    def test_compress_decompress_bzip2(self):
        compressed = self.manager.compress(self.test_data, format="bzip2")
        self.assertTrue(compressed.startswith(b"BZh"))
        decompressed = self.manager.decompress(compressed, format="bzip2")
        self.assertEqual(decompressed, self.test_data)

    def test_compress_decompress_lzma(self):
        compressed = self.manager.compress(self.test_data, format="lzma")
        self.assertTrue(compressed.startswith(b"\xfd\x37\x7a\x58\x5a\x00"))
        decompressed = self.manager.decompress(compressed, format="lzma")
        self.assertEqual(decompressed, self.test_data)

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            self.manager.compress(self.test_data, format="invalid")
        with self.assertRaises(ValueError):
            self.manager.decompress(self.test_data, format="invalid")


class TestZlibLabLogic(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_compress_hex(self, mock_stdout):
        args = argparse.Namespace(compress="hello world", decompress=None, format="zlib", base64=False, tui=False)
        self.assertTrue(run_zlib_lab_logic(args))
        output = mock_stdout.getvalue().strip()
        # Should be a hex string
        self.assertTrue(all(c in "0123456789abcdefABCDEF" for c in output))
        self.assertTrue(len(output) > 0)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_compress_base64(self, mock_stdout):
        args = argparse.Namespace(compress="hello world", decompress=None, format="zlib", base64=True, tui=False)
        self.assertTrue(run_zlib_lab_logic(args))
        output = mock_stdout.getvalue().strip()
        # Should be valid base64
        decoded = base64.b64decode(output)
        self.assertTrue(len(decoded) > 0)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_decompress_hex(self, mock_stdout):
        manager = ZlibLabManager()
        compressed = manager.compress(b"hello world", format="zlib")
        args = argparse.Namespace(compress=None, decompress=compressed.hex(), format="zlib", base64=False, tui=False)
        self.assertTrue(run_zlib_lab_logic(args))
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, "hello world")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_decompress_base64(self, mock_stdout):
        manager = ZlibLabManager()
        compressed = manager.compress(b"hello world", format="zlib")
        b64_str = base64.b64encode(compressed).decode("ascii")
        args = argparse.Namespace(compress=None, decompress=b64_str, format="zlib", base64=True, tui=False)
        self.assertTrue(run_zlib_lab_logic(args))
        output = mock_stdout.getvalue().strip()
        self.assertEqual(output, "hello world")

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_run_no_args(self, mock_stderr):
        args = argparse.Namespace(compress=None, decompress=None, tui=False)
        self.assertFalse(run_zlib_lab_logic(args))
        self.assertIn("Error: must provide either --compress, --decompress, or --tui", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
