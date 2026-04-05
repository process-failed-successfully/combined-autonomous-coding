import unittest
import tempfile
import os
import shutil
from pathlib import Path
from shared.hex_lab import HexManager

class TestHexManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = HexManager(Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_and_read(self):
        # Create dummy file
        file_path = Path(self.temp_dir) / "test.bin"
        file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        self.manager.load_file(file_path)
        self.assertEqual(self.manager.get_size(), 6)

        chunk = self.manager.read_chunk(0, 4)
        self.assertEqual(chunk, b"\x00\x01\x02\x03")

        chunk = self.manager.read_chunk(4, 4)
        self.assertEqual(chunk, b"\x04\x05")

    def test_write_and_save(self):
        file_path = Path(self.temp_dir) / "test.bin"
        file_path.write_bytes(b"\x00\x00\x00")

        self.manager.load_file(file_path)
        self.manager.write_byte(1, 0xFF)

        # Check in memory
        self.assertEqual(self.manager.read_chunk(0, 3), b"\x00\xFF\x00")

        # Save
        self.manager.save_file()

        # Check on disk
        content = file_path.read_bytes()
        self.assertEqual(content, b"\x00\xFF\x00")

    def test_large_file_limit(self):
        file_path = Path(self.temp_dir) / "large.bin"
        # 11 MB
        with open(file_path, "wb") as f:
            f.seek(11 * 1024 * 1024 - 1)
            f.write(b"\0")

        with self.assertRaises(ValueError):
            self.manager.load_file(file_path)

if __name__ == '__main__':
    unittest.main()
