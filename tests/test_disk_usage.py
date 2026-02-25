import shutil
import tempfile
import unittest
from pathlib import Path
import os
from shared.disk_usage import scan_disk_usage, get_largest_files, format_size

class TestDiskUsage(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = Path(tempfile.mkdtemp())

        # Create structure:
        # root/
        #   file1.txt (10 bytes)
        #   dir1/
        #     file2.txt (20 bytes)
        #   dir2/
        #     file3.txt (30 bytes)
        #     subdir/
        #       file4.txt (40 bytes)
        #   link_to_file1 -> file1.txt

        self.file1 = self.test_dir / "file1.txt"
        self.file1.write_text("a" * 10)

        self.dir1 = self.test_dir / "dir1"
        self.dir1.mkdir()
        self.file2 = self.dir1 / "file2.txt"
        self.file2.write_text("b" * 20)

        self.dir2 = self.test_dir / "dir2"
        self.dir2.mkdir()
        self.file3 = self.dir2 / "file3.txt"
        self.file3.write_text("c" * 30)

        self.subdir = self.dir2 / "subdir"
        self.subdir.mkdir()
        self.file4 = self.subdir / "file4.txt"
        self.file4.write_text("d" * 40)

        # Symlink
        self.link = self.test_dir / "link_to_file1"
        try:
            self.link.symlink_to(self.file1)
        except OSError:
            # Skip symlink creation if not supported (e.g. Windows without admin)
            self.link = None

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_disk_usage_total_size(self):
        result = scan_disk_usage(self.test_dir)

        # Total size = 10 + 20 + 30 + 40 = 100 bytes
        # Symlinks should be skipped
        self.assertEqual(result["size"], 100)
        self.assertEqual(result["name"], self.test_dir.name)
        self.assertEqual(result["type"], "dir")

    def test_scan_disk_usage_structure(self):
        result = scan_disk_usage(self.test_dir)

        # Check children count (file1, dir1, dir2) - link is skipped
        # children are sorted by size descending
        children = result["children"]
        self.assertTrue(len(children) >= 3)

        # Find dir2 (should be largest: 30+40 = 70)
        dir2_node = next((c for c in children if c["name"] == "dir2"), None)
        self.assertIsNotNone(dir2_node)
        self.assertEqual(dir2_node["size"], 70)

        # Check dir2 children
        dir2_children = dir2_node["children"]
        subdir_node = next((c for c in dir2_children if c["name"] == "subdir"), None)
        self.assertIsNotNone(subdir_node)
        self.assertEqual(subdir_node["size"], 40)

    def test_get_largest_files(self):
        files = get_largest_files(self.test_dir, limit=2)

        # Largest should be file4.txt (40), then file3.txt (30)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["name"], "file4.txt")
        self.assertEqual(files[0]["size"], 40)
        self.assertEqual(files[1]["name"], "file3.txt")
        self.assertEqual(files[1]["size"], 30)

    def test_format_size(self):
        self.assertEqual(format_size(100), "100.0 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024), "1.0 MB")

if __name__ == "__main__":
    unittest.main()
