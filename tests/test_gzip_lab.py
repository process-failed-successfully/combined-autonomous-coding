import os
import tempfile
import unittest
from pathlib import Path

from shared.gzip_lab import GzipLabManager

class TestGzipLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = GzipLabManager()

    def test_compress_decompress_bytes(self):
        original_data = b"Hello, World! This is a test string to be compressed."
        compressed_data = self.manager.compress_bytes(original_data)

        self.assertNotEqual(original_data, compressed_data)
        self.assertTrue(len(compressed_data) > 0)

        decompressed_data = self.manager.decompress_bytes(compressed_data)
        self.assertEqual(original_data, decompressed_data)

    def test_compress_decompress_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.txt"
            compressed_path = Path(temp_dir) / "input.txt.gz"
            output_path = Path(temp_dir) / "output.txt"

            original_data = b"This is some test data to compress to a file.\nIt has multiple lines.\n"
            with open(input_path, "wb") as f:
                f.write(original_data)

            self.manager.compress_file(input_path, compressed_path)

            self.assertTrue(compressed_path.exists())
            self.assertTrue(os.path.getsize(compressed_path) > 0)

            self.manager.decompress_file(compressed_path, output_path)

            self.assertTrue(output_path.exists())

            with open(output_path, "rb") as f:
                decompressed_data = f.read()

            self.assertEqual(original_data, decompressed_data)

if __name__ == "__main__":
    unittest.main()
