import unittest
from pathlib import Path
import tempfile
import argparse
from io import StringIO
from unittest.mock import patch

from shared.tree_lab import TreeLabManager, run_tree_lab_logic


class TestTreeLabManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)

        # Create a sample structure
        # temp_dir/
        # ├── a_dir/
        # │   └── file_in_a.txt
        # ├── .git/
        # │   └── config
        # ├── b_file.txt
        # └── c_dir/

        (self.temp_dir / "a_dir").mkdir()
        (self.temp_dir / "a_dir" / "file_in_a.txt").touch()

        (self.temp_dir / ".git").mkdir()
        (self.temp_dir / ".git" / "config").touch()

        (self.temp_dir / "b_file.txt").touch()

        (self.temp_dir / "c_dir").mkdir()

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_default_excludes(self):
        manager = TreeLabManager()
        tree_str = manager.generate_tree(self.temp_dir)

        # Expected structure (sorted: dirs first, then files):
        # ├── a_dir
        # │   └── file_in_a.txt
        # ├── c_dir
        # └── b_file.txt

        self.assertIn("├── a_dir", tree_str)
        self.assertIn("│   └── file_in_a.txt", tree_str)
        self.assertIn("├── c_dir", tree_str)
        self.assertIn("└── b_file.txt", tree_str)

        # .git should be excluded
        self.assertNotIn(".git", tree_str)

    def test_custom_excludes(self):
        manager = TreeLabManager(exclude=["c_dir"])
        tree_str = manager.generate_tree(self.temp_dir)

        self.assertNotIn("c_dir", tree_str)
        self.assertIn(".git", tree_str)
        self.assertIn("a_dir", tree_str)

    def test_max_depth_0(self):
        manager = TreeLabManager()
        tree_str = manager.generate_tree(self.temp_dir, max_depth=0)

        # Should only show the top level entries, not the children
        self.assertIn("├── a_dir", tree_str)
        self.assertNotIn("file_in_a.txt", tree_str)

    def test_run_tree_lab_logic(self):
        args = argparse.Namespace(dir=str(self.temp_dir), max_depth=-1, exclude=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            run_tree_lab_logic(args)
            output = mock_stdout.getvalue()

            self.assertTrue(output.startswith(f"{self.temp_dir.resolve().name}/"))
            self.assertIn("a_dir", output)
            self.assertNotIn(".git", output)
