import unittest
import tempfile
import os
from pathlib import Path
from shared.hash_lab import HashLabManager

class TestHashLab(unittest.TestCase):

    def setUp(self):
        self.manager = HashLabManager()
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_hash_string(self):
        # Known SHA256 for "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(self.manager.hash_string("hello"), expected)
        self.assertEqual(self.manager.hash_string("hello", "sha256"), expected)

        # MD5 for "hello"
        expected_md5 = "5d41402abc4b2a76b9719d911017c592"
        self.assertEqual(self.manager.hash_string("hello", "md5"), expected_md5)

    def test_hash_file(self):
        f = self.root / "test.txt"
        f.write_text("hello", encoding="utf-8")

        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(self.manager.hash_file(f), expected)

    def test_hash_dir(self):
        f1 = self.root / "file1.txt"
        f1.write_text("a", encoding="utf-8")
        f2 = self.root / "file2.txt"
        f2.write_text("b", encoding="utf-8")

        # Subdir
        d = self.root / "sub"
        d.mkdir()
        f3 = d / "file3.txt"
        f3.write_text("c", encoding="utf-8")

        # Non-recursive
        res = self.manager.hash_dir(self.root, recursive=False)
        self.assertIn(str(f1), res)
        self.assertIn(str(f2), res)
        self.assertNotIn(str(f3), res)

        # Recursive
        res = self.manager.hash_dir(self.root, recursive=True)
        self.assertIn(str(f1), res)
        self.assertIn(str(f2), res)
        self.assertIn(str(f3), res)

    def test_compare_files(self):
        f1 = self.root / "f1.txt"
        f1.write_text("data", encoding="utf-8")

        f2 = self.root / "f2.txt"
        f2.write_text("data", encoding="utf-8")

        f3 = self.root / "f3.txt"
        f3.write_text("diff", encoding="utf-8")

        res_match = self.manager.compare_files(f1, f2)
        self.assertTrue(res_match["match"])
        self.assertEqual(res_match["hash1"], res_match["hash2"])

        res_diff = self.manager.compare_files(f1, f3)
        self.assertFalse(res_diff["match"])
        self.assertNotEqual(res_diff["hash1"], res_diff["hash2"])

    def test_verify_checksums(self):
        f1 = self.root / "file1.txt"
        f1.write_text("content1", encoding="utf-8")
        h1 = self.manager.hash_file(f1, "sha256")

        f2 = self.root / "file2.txt"
        f2.write_text("content2", encoding="utf-8")
        h2 = self.manager.hash_file(f2, "sha256")

        # Create checksum file
        checksum_file = self.root / "sums.txt"
        with open(checksum_file, "w") as f:
            f.write(f"{h1}  file1.txt\n")
            f.write(f"{h2}  file2.txt\n")

        # Verify
        res = self.manager.verify_checksums(checksum_file)
        self.assertEqual(len(res["passed"]), 2)
        self.assertEqual(len(res["failed"]), 0)
        self.assertEqual(len(res["missing"]), 0)

        # Tamper
        f2.write_text("modified", encoding="utf-8")
        res = self.manager.verify_checksums(checksum_file)
        self.assertEqual(len(res["passed"]), 1)
        self.assertEqual(len(res["failed"]), 1)
        self.assertEqual(res["failed"][0]["file"], "file2.txt")

if __name__ == '__main__':
    unittest.main()
