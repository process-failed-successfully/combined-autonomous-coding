import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
from pathlib import Path
import os
import shutil
import tempfile

# Add project root to sys.path to allow importing main
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from main import run_revert

class TestMainRevert(unittest.TestCase):
    def setUp(self):
        """Set up a temporary git repository for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create and commit initial files
        self.initial_files = {
            "file1.txt": "Initial content for file1.",
            "file2.txt": "Initial content for file2.",
            "dir1/file3.txt": "Initial content for file3 in dir1."
        }
        for file_path, content in self.initial_files.items():
            path = self.project_dir / file_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True, capture_output=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _get_git_status(self):
        """Helper to get the output of git status --porcelain."""
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    @patch('builtins.input', return_value='y')
    @patch('sys.exit')
    def test_revert_all_changes(self, mock_exit, mock_input):
        """Test reverting all uncommitted changes."""
        # 1. Modify a tracked file
        (self.project_dir / "file1.txt").write_text("Modified content.")
        # 2. Create an untracked file
        (self.project_dir / "new_file.txt").write_text("This is a new file.")
        # 3. Create a new directory with a file
        (self.project_dir / "dir2").mkdir()
        (self.project_dir / "dir2/new_file2.txt").write_text("Another new file.")

        # Check that changes are present
        status_before = self._get_git_status()
        self.assertIn("M file1.txt", status_before)
        self.assertIn("?? new_file.txt", status_before)
        self.assertIn("?? dir2/", status_before)

        # Run revert command for all files
        args = MagicMock()
        args.project_dir = self.project_dir
        args.files = []
        args.yes = True  # Skip confirmation for tests
        run_revert(args)

        # Check that the working directory is clean
        status_after = self._get_git_status()
        self.assertEqual(status_after, "")

        # Check that the modified file is back to its original state
        content = (self.project_dir / "file1.txt").read_text()
        self.assertEqual(content, self.initial_files["file1.txt"])

        # Check that the new files and directory are gone
        self.assertFalse((self.project_dir / "new_file.txt").exists())
        self.assertFalse((self.project_dir / "dir2").exists())
        mock_exit.assert_called_with(0)

    @patch('builtins.input', return_value='y')
    @patch('sys.exit')
    def test_revert_specific_files(self, mock_exit, mock_input):
        """Test reverting only specified files."""
        # 1. Modify two tracked files
        (self.project_dir / "file1.txt").write_text("Modified content for file1.")
        (self.project_dir / "file2.txt").write_text("Modified content for file2.")
        # 2. Create two untracked files
        (self.project_dir / "untracked1.txt").write_text("Untracked file 1.")
        (self.project_dir / "untracked2.txt").write_text("Untracked file 2.")

        # Check that changes are present
        status_before = self._get_git_status()
        self.assertIn("M file1.txt", status_before)
        self.assertIn("M file2.txt", status_before)
        self.assertIn("?? untracked1.txt", status_before)
        self.assertIn("?? untracked2.txt", status_before)

        # Run revert command for one modified and one untracked file
        args = MagicMock()
        args.project_dir = self.project_dir
        args.files = ["file1.txt", "untracked1.txt"]
        args.yes = True
        run_revert(args)

        # Check the git status after reverting
        status_after = self._get_git_status()
        self.assertNotIn("M file1.txt", status_after)
        self.assertNotIn("?? untracked1.txt", status_after)
        self.assertIn("M file2.txt", status_after)  # Should remain modified
        self.assertIn("?? untracked2.txt", status_after) # Should remain untracked

        # Check file contents and existence
        self.assertEqual((self.project_dir / "file1.txt").read_text(), self.initial_files["file1.txt"])
        self.assertEqual((self.project_dir / "file2.txt").read_text(), "Modified content for file2.")
        self.assertFalse((self.project_dir / "untracked1.txt").exists())
        self.assertTrue((self.project_dir / "untracked2.txt").exists())
        mock_exit.assert_called_with(0)

    @patch('sys.exit')
    def test_revert_no_changes(self, mock_exit):
        """Test revert command when there are no uncommitted changes."""
        # Ensure the directory is clean
        self.assertEqual(self._get_git_status(), "")

        # Run revert for all files
        args = MagicMock()
        args.project_dir = self.project_dir
        args.files = []
        args.yes = True
        run_revert(args)

        # Should exit gracefully
        mock_exit.assert_called_with(0)
        self.assertEqual(self._get_git_status(), "") # Still clean

        # Run revert for specific files
        args.files = ["file1.txt"]
        run_revert(args)
        mock_exit.assert_called_with(0)
        self.assertEqual(self._get_git_status(), "") # Still clean

if __name__ == '__main__':
    unittest.main()