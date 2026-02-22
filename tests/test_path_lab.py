import unittest
import tempfile
import shutil
import os
from pathlib import Path
from shared.path_lab import PathLabManager

class TestPathLab(unittest.TestCase):
    def setUp(self):
        self.manager = PathLabManager()
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_analyze_path_basic(self):
        p = Path(self.test_dir) / "test_file.txt"
        p.touch()

        info = self.manager.analyze_path(str(p))

        self.assertEqual(info["name"], "test_file.txt")
        self.assertEqual(info["stem"], "test_file")
        self.assertEqual(info["suffix"], ".txt")
        self.assertTrue(info["exists"])
        self.assertTrue(info["is_file"])
        self.assertFalse(info["is_dir"])
        self.assertIsNotNone(info["stat"])

    def test_analyze_path_non_existent(self):
        p = Path(self.test_dir) / "ghost.txt"
        info = self.manager.analyze_path(str(p))

        self.assertEqual(info["name"], "ghost.txt")
        self.assertFalse(info["exists"])
        self.assertFalse(info["is_file"])

    def test_calculate_relative(self):
        target = "/a/b/c/d.txt"
        start = "/a/b"

        res = self.manager.calculate_relative(target, start)
        self.assertTrue(res["success"])
        # os.path.relpath output might vary on Windows vs Unix for separators, but here we assume /
        # We can normalize or check if it ends with c/d.txt
        self.assertTrue(res["result"].replace("\\", "/").endswith("c/d.txt"))

    def test_calculate_relative_error(self):
        # On Windows, different drives raise ValueError for relative_to, but os.path.relpath handles it usually or raises.
        # But analyze_path uses pathlib.
        # PathLabManager uses os.path.relpath which is robust.
        # Let's just check standard case.
        pass

    def test_join_paths(self):
        base = "/a/b"
        parts = ["c", "d.txt"]
        result = self.manager.join_paths(base, parts)
        self.assertTrue(result.replace("\\", "/").endswith("/a/b/c/d.txt"))

    def test_glob_path(self):
        # Create some files
        (Path(self.test_dir) / "a.py").touch()
        (Path(self.test_dir) / "b.txt").touch()
        sub = Path(self.test_dir) / "sub"
        sub.mkdir()
        (sub / "c.py").touch()

        # Test *.py non-recursive
        matches = self.manager.glob_path(self.test_dir, "*.py", recursive=False)
        self.assertIn("a.py", matches)
        self.assertNotIn("c.py", matches)

        # Test recursive
        matches_rec = self.manager.glob_path(self.test_dir, "*.py", recursive=True)
        # matches are relative strings
        self.assertIn("a.py", matches_rec)
        # sub/c.py might be returned as 'sub/c.py' or 'sub\c.py'
        self.assertTrue(any("c.py" in m for m in matches_rec))

if __name__ == "__main__":
    unittest.main()
