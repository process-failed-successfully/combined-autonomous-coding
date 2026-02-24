import unittest
import os
import time
import shutil
import tempfile
from pathlib import Path
from shared.find_lab import FindLabManager

class TestFindLab(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = FindLabManager(Path(self.test_dir))

        # Create structure:
        # root/
        #   small.txt (10 bytes)
        #   large.bin (1MB)
        #   old.log (mtime - 2 days)
        #   new.log (mtime now)
        #   subdir/
        #     nested.py

        self.small_file = Path(self.test_dir) / "small.txt"
        self.small_file.write_bytes(b"x" * 10)

        self.large_file = Path(self.test_dir) / "large.bin"
        with open(self.large_file, "wb") as f:
            f.seek(1024 * 1024 - 1)
            f.write(b"\0")

        self.old_file = Path(self.test_dir) / "old.log"
        self.old_file.touch()
        # Set mtime to 2 days ago
        two_days_ago = time.time() - (2 * 86400)
        os.utime(self.old_file, (two_days_ago, two_days_ago))

        self.new_file = Path(self.test_dir) / "new.log"
        self.new_file.touch()

        self.subdir = Path(self.test_dir) / "subdir"
        self.subdir.mkdir()
        self.nested_file = self.subdir / "nested.py"
        self.nested_file.touch()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parse_size(self):
        op, val = self.manager._parse_size(">1M")
        self.assertEqual(op, ">")
        self.assertEqual(val, 1024 * 1024)

        op, val = self.manager._parse_size("< 10k")
        self.assertEqual(op, "<")
        self.assertEqual(val, 10 * 1024)

        op, val = self.manager._parse_size("500")
        self.assertEqual(op, "=")
        self.assertEqual(val, 500)

    def test_parse_time(self):
        # >1d means older than 1 day (timestamp < threshold)
        op, thresh = self.manager._parse_time(">1d")
        self.assertEqual(op, ">")
        # Threshold should be roughly now - 86400
        self.assertAlmostEqual(thresh, time.time() - 86400, delta=5)

    def test_find_by_name(self):
        results = list(self.manager.find_files(name_pattern="*.log"))
        self.assertEqual(len(results), 2)
        self.assertIn(self.old_file, results)
        self.assertIn(self.new_file, results)

        results = list(self.manager.find_files(name_pattern="nested.*"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.nested_file)

    def test_find_by_regex(self):
        # Find files ending in .txt or .bin
        results = list(self.manager.find_files(regex_pattern=r".*\.(txt|bin)$"))
        self.assertEqual(len(results), 2)
        self.assertIn(self.small_file, results)
        self.assertIn(self.large_file, results)

    def test_find_by_size(self):
        # > 500k
        results = list(self.manager.find_files(size_filter=">500k"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], self.large_file)

        # < 100b
        # Includes empty files? new.log, old.log, nested.py are empty (0 bytes)
        # small.txt is 10 bytes.
        results = list(self.manager.find_files(size_filter="<100b"))
        # Should contain small.txt, old.log, new.log, nested.py
        self.assertIn(self.small_file, results)
        self.assertNotIn(self.large_file, results)

    def test_find_by_time(self):
        # Older than 1 day
        results = list(self.manager.find_files(time_filter=">1d"))
        self.assertIn(self.old_file, results)
        self.assertNotIn(self.new_file, results)

        # Newer than 1 hour
        results = list(self.manager.find_files(time_filter="<1h"))
        self.assertIn(self.new_file, results)
        self.assertNotIn(self.old_file, results)

    def test_find_by_type(self):
        # Directories
        results = list(self.manager.find_files(type_filter="d"))
        self.assertIn(self.subdir, results)
        self.assertNotIn(self.small_file, results)

        # Files
        results = list(self.manager.find_files(type_filter="f"))
        self.assertIn(self.small_file, results)
        self.assertNotIn(self.subdir, results)

    def test_find_by_extension(self):
        results = list(self.manager.find_files(extensions="py,txt"))
        self.assertEqual(len(results), 2)
        self.assertIn(self.small_file, results)
        self.assertIn(self.nested_file, results)

if __name__ == '__main__':
    unittest.main()
