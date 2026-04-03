import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from shared.hash_lab import HashLabManager, run_hash_lab_logic

class TestHashLab(unittest.TestCase):
    def setUp(self):
        self.manager = HashLabManager()
        self.test_dir = Path(tempfile.mkdtemp())
        self.file1 = self.test_dir / "file1.txt"
        self.file2 = self.test_dir / "file2.txt"
        self.file1.write_text("hello")
        self.file2.write_text("world")

        self.checksum_file = self.test_dir / "checksums.txt"
        h1 = self.manager.hash_string("hello", "sha256")
        h2 = self.manager.hash_string("world", "sha256")
        self.checksum_file.write_text(f"{h1}  file1.txt\n{h2}  file2.txt\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_hash_string(self):
        h = self.manager.hash_string("hello", "sha256")
        self.assertEqual(h, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_hash_file(self):
        h = self.manager.hash_file(self.file1, "sha256")
        self.assertEqual(h, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_hash_dir(self):
        res = self.manager.hash_dir(self.test_dir, "sha256")
        self.assertIn(str(self.file1), res)
        self.assertIn(str(self.file2), res)

    def test_compare_files(self):
        res = self.manager.compare_files(self.file1, self.file1, "sha256")
        self.assertTrue(res["match"])

        res2 = self.manager.compare_files(self.file1, self.file2, "sha256")
        self.assertFalse(res2["match"])

    def test_verify_checksums(self):
        res = self.manager.verify_checksums(self.checksum_file, "sha256")
        self.assertEqual(len(res["passed"]), 2)
        self.assertEqual(len(res["failed"]), 0)

