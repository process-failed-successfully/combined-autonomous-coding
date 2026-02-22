import unittest
from pathlib import Path
import tempfile
import shutil
import os
from shared.path_lab import PathLabManager

class TestPathLabManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.manager = PathLabManager(Path(self.test_dir))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_inspect_path_exists(self):
        p = Path(self.test_dir) / "test_file.txt"
        p.write_text("hello")

        info = self.manager.inspect_path(str(p))
        self.assertTrue(info["exists"])
        self.assertTrue(info["is_file"])
        self.assertEqual(info["name"], "test_file.txt")
        self.assertEqual(info["suffix"], ".txt")
        self.assertEqual(info["size"], 5)

    def test_inspect_path_not_exists(self):
        p = Path(self.test_dir) / "non_existent.txt"
        info = self.manager.inspect_path(str(p))
        self.assertFalse(info["exists"])
        self.assertEqual(info["name"], "non_existent.txt")

    def test_calculate_relative(self):
        target = "/a/b/c/d.txt"
        start = "/a/b"
        # On Windows, this might fail if drive letters differ, but assuming posix style or same drive
        # We can use os.path.join to be safe or relative logic

        rel = self.manager.calculate_relative(target, start)
        # Expected: c/d.txt (on unix) or c\d.txt (on windows)
        expected = os.path.join("c", "d.txt")
        self.assertEqual(rel, expected)

    def test_join_paths(self):
        paths = ["a", "b", "c.txt"]
        joined = self.manager.join_paths(paths)
        expected = os.path.join("a", "b", "c.txt")
        self.assertEqual(joined, expected)

    def test_glob_search(self):
        # Setup files
        (Path(self.test_dir) / "a.py").touch()
        (Path(self.test_dir) / "b.txt").touch()
        subdir = Path(self.test_dir) / "sub"
        subdir.mkdir()
        (subdir / "c.py").touch()

        # Test *.py
        results = self.manager.glob_search(self.test_dir, "*.py")
        self.assertIn("a.py", results)
        self.assertNotIn("b.txt", results)
        self.assertNotIn(os.path.join("sub", "c.py"), results) # Non-recursive

        # Test recursive
        results_rec = self.manager.glob_search(self.test_dir, "**/*.py", recursive=True)
        # pathlib.glob('**/*.py') should find both
        # Note: glob_search uses base.glob(pattern). If pattern has **, it is recursive.

        results_manual_rec = self.manager.glob_search(self.test_dir, "**/*.py")
        self.assertIn("a.py", results_manual_rec)
        self.assertIn(os.path.join("sub", "c.py"), results_manual_rec)

if __name__ == '__main__':
    unittest.main()
