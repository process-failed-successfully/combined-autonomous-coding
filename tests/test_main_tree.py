import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from pathlib import Path
import os
import tempfile
import shutil

# This is a bit of a hack to make sure we can import from the parent directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_tree

class TestTreeCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.original_stdout = sys.stdout
        sys.stdout = self.captured_output = io.StringIO()

        # Create a test structure
        (self.project_dir / "file1.txt").touch()
        (self.project_dir / "dir1").mkdir()
        (self.project_dir / "dir1" / "file2.txt").touch()
        (self.project_dir / "dir2").mkdir()
        (self.project_dir / "dir2" / "dir3").mkdir()
        (self.project_dir / "dir2" / "dir3" / "file3.txt").touch()
        (self.project_dir / ".git").mkdir()
        (self.project_dir / ".git" / "config").touch()
        (self.project_dir / "__pycache__").mkdir()
        (self.project_dir / "__pycache__" / "cache.pyc").touch()
        (self.project_dir / "empty_dir").mkdir()


    def tearDown(self):
        sys.stdout = self.original_stdout
        shutil.rmtree(self.test_dir)

    def _run_tree_and_get_output(self, depth=3, full=False):
        """Helper to run the tree command and return the captured output."""
        args = MagicMock()
        args.project_dir = self.project_dir
        args.depth = depth
        args.full = full
        with self.assertRaises(SystemExit) as cm:
            run_tree(args)
        self.assertEqual(cm.exception.code, 0)
        return self.captured_output.getvalue()

    def test_tree_default_output(self):
        """Test the default tree output, ignoring artifacts and with default depth."""
        output = self._run_tree_and_get_output()

        # Check that the header is correct
        self.assertIn(f"--- Tree view of: {self.project_dir.resolve()} ---", output)

        # Check that ignored directories are not present
        self.assertNotIn(".git", output)
        self.assertNotIn("__pycache__", output)

        # Check that expected files and directories are present
        self.assertIn("dir1/", output)
        self.assertIn("file2.txt", output)
        self.assertIn("dir2/", output)
        self.assertIn("dir3/", output)
        self.assertIn("file3.txt", output)
        self.assertIn("empty_dir/", output)
        self.assertIn("file1.txt", output)

    def test_tree_with_depth_limit(self):
        """Test the --depth argument to limit recursion."""
        output = self._run_tree_and_get_output(depth=1)

        # Should see top-level files and dirs
        self.assertIn("dir1/", output)
        self.assertIn("dir2/", output)
        self.assertIn("file1.txt", output)

        # Should NOT see files inside dir1 or dir2
        self.assertNotIn("file2.txt", output)
        self.assertNotIn("dir3/", output)
        self.assertNotIn("file3.txt", output)

    def test_tree_with_full_flag(self):
        """Test the --full flag to include ignored directories."""
        output = self._run_tree_and_get_output(full=True)

        # Check that normally ignored directories are now present
        self.assertIn(".git/", output)
        self.assertIn("__pycache__/", output)

        # Check that files within those directories are also present
        self.assertIn("config", output)
        self.assertIn("cache.pyc", output)

    def test_tree_handles_empty_directories(self):
        """Test that empty directories are correctly displayed."""
        output = self._run_tree_and_get_output()

        # The output should contain the empty directory name
        self.assertIn("empty_dir/", output)


if __name__ == '__main__':
    unittest.main()
