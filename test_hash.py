import unittest
from shared.hash_lab import HashLabManager
import os
import tempfile
from pathlib import Path

class TestHashLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = HashLabManager()
        self.test_dir = tempfile.mkdtemp()
        self.test_file1 = os.path.join(self.test_dir, "file1.txt")
        self.test_file2 = os.path.join(self.test_dir, "file2.txt")
        with open(self.test_file1, "w") as f:
            f.write("hello")
        with open(self.test_file2, "w") as f:
            f.write("world")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_hash_string(self):
        h = self.manager.hash_string("hello", "sha256")
        self.assertEqual(h, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_hash_file(self):
        h = self.manager.hash_file(self.test_file1, "sha256")
        self.assertEqual(h, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

if __name__ == "__main__":
    unittest.main()
