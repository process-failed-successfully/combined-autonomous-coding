import unittest
import argparse
import base64
import io
from unittest.mock import patch

from shared.zstd_lab import ZstdLabManager, run_zstd_lab_logic

class TestZstdLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ZstdLabManager()
        self.test_data = b"Hello, Zstandard Compression!"

    def test_compress_decompress_default(self):
        compressed = self.manager.compress(self.test_data)
        self.assertNotEqual(compressed, self.test_data)
        self.assertTrue(len(compressed) > 0)

        decompressed = self.manager.decompress(compressed)
        self.assertEqual(decompressed, self.test_data)

    def test_compress_decompress_level(self):
        # Using a very high compression level just to see it doesn't fail
        compressed = self.manager.compress(self.test_data, level=10)
        self.assertNotEqual(compressed, self.test_data)

        decompressed = self.manager.decompress(compressed)
        self.assertEqual(decompressed, self.test_data)


class TestZstdLabLogic(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_compress_hex(self, mock_stdout):
        args = argparse.Namespace(compress="test text", decompress=None, level=3, base64=False, tui=False)
        self.assertTrue(run_zstd_lab_logic(args))
        output = mock_stdout.getvalue().strip()
        self.assertTrue(all(c in "0123456789abcdefABCDEF" for c in output))
        self.assertTrue(len(output) > 0)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_compress_base64(self, mock_stdout):
        args = argparse.Namespace(compress="test text", decompress=None, level=3, base64=True, tui=False)
        self.assertTrue(run_zstd_lab_logic(args))
        output = mock_stdout.getvalue().strip()
        decoded = base64.b64decode(output)
        self.assertTrue(len(decoded) > 0)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_decompress_hex(self, mock_stdout):
        manager = ZstdLabManager()
        compressed = manager.compress(b"test text")
        hex_data = compressed.hex()

        args = argparse.Namespace(compress=None, decompress=hex_data, level=3, base64=False, tui=False)
        self.assertTrue(run_zstd_lab_logic(args))
        self.assertEqual(mock_stdout.getvalue().strip(), "test text")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_decompress_base64(self, mock_stdout):
        manager = ZstdLabManager()
        compressed = manager.compress(b"test text")
        b64_data = base64.b64encode(compressed).decode("ascii")

        args = argparse.Namespace(compress=None, decompress=b64_data, level=3, base64=True, tui=False)
        self.assertTrue(run_zstd_lab_logic(args))
        self.assertEqual(mock_stdout.getvalue().strip(), "test text")

if __name__ == '__main__':
    unittest.main()
