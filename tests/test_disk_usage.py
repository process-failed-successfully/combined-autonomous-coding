import unittest
import tempfile
import shutil
import os
from pathlib import Path
from shared.disk_usage import scan_disk_usage, format_size, get_largest_files

class TestDiskUsage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)

        # Create some files
        (self.root / "file1.txt").write_text("a" * 1024) # 1KB
        (self.root / "file2.txt").write_text("b" * 2048) # 2KB

        # Create subdir
        sub = self.root / "subdir"
        sub.mkdir()
        (sub / "file3.txt").write_text("c" * 512) # 512B

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_format_size(self):
        self.assertEqual(format_size(500), "500.0 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(format_size(1024 * 1024 * 1024), "1.0 GB")

    def test_scan_disk_usage(self):
        data = scan_disk_usage(self.root)

        self.assertEqual(data["name"], Path(self.test_dir).name)
        self.assertEqual(data["type"], "dir")
        # Total size: 1024 + 2048 + 512 = 3584
        self.assertEqual(data["size"], 3584)

        children = data["children"]
        self.assertEqual(len(children), 3) # file1, file2, subdir

        # Check sorting (descending size)
        # file2 (2048) > file1 (1024) > subdir (512)
        self.assertEqual(children[0]["name"], "file2.txt")
        self.assertEqual(children[0]["size"], 2048)

        self.assertEqual(children[1]["name"], "file1.txt")
        self.assertEqual(children[1]["size"], 1024)

        self.assertEqual(children[2]["name"], "subdir")
        self.assertEqual(children[2]["size"], 512)

        # Check subdir children
        subdir_node = children[2]
        self.assertEqual(len(subdir_node["children"]), 1)
        self.assertEqual(subdir_node["children"][0]["name"], "file3.txt")

    def test_get_largest_files(self):
        files = get_largest_files(self.root, limit=2)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["name"], "file2.txt")
        self.assertEqual(files[1]["name"], "file1.txt")

if __name__ == "__main__":
    unittest.main()
