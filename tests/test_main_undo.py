import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys

# Ensure the main script can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_discard, run_undo


class TestMainUndoCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

        self.git_path = shutil.which("git")
        if not self.git_path:
            self.fail("Git executable not found in PATH")

        # Initialize a git repository
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create and commit initial files
        (self.project_dir / "file1.txt").write_text("This is file 1.")
        (self.project_dir / "file2.txt").write_text("This is file 2.")
        subprocess.run([self.git_path, "add", "."], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.input')
    def test_interactive_undo_and_partial_restore(self, mock_input):
        # 1. Create uncommitted changes (1 modified, 1 untracked)
        (self.project_dir / "file1.txt").write_text("This is file 1 with modifications.")
        (self.project_dir / "new_file.txt").write_text("This is a new untracked file.")

        # 2. Run 'discard' to stash the changes
        discard_args = MagicMock()
        discard_args.project_dir = self.project_dir
        discard_args.files = []
        discard_args.interactive = False
        discard_args.yes = True  # Automatically confirm discard

        with self.assertRaises(SystemExit) as cm:
            run_discard(discard_args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that the working directory is clean
        status_result = subprocess.run(
            [self.git_path, "status", "--porcelain"],
            cwd=self.project_dir, capture_output=True, text=True, check=True
        )
        self.assertEqual(status_result.stdout, "")

        # 3. Run 'undo' and simulate interactive session for partial restore
        undo_args = MagicMock()
        undo_args.project_dir = self.project_dir

        # Simulate user input:
        # 1. Select the first (and only) stash
        # 2. Choose option '4' (Restore specific files)
        # 3. Enter the path of the file to restore ('file1.txt')
        # 4. Confirm the restore ('y')
        # 5. Choose 'q' to quit the interactive manager
        mock_input.side_effect = ['1', '4', 'file1.txt', 'y', 'q']

        with self.assertRaises(SystemExit) as cm:
            run_undo(undo_args)
        self.assertEqual(cm.exception.code, 0)

        # 4. Assertions
        # Check that only file1.txt was restored
        self.assertEqual((self.project_dir / "file1.txt").read_text(), "This is file 1 with modifications.")
        self.assertFalse((self.project_dir / "new_file.txt").exists())

        # Check that the stash still exists (since we did a partial restore)
        stash_list_result = subprocess.run(
            [self.git_path, "stash", "list"],
            cwd=self.project_dir, capture_output=True, text=True, check=True
        )
        self.assertIn("agent-discard-stash", stash_list_result.stdout)

    @patch('builtins.input')
    def test_interactive_undo_and_full_restore(self, mock_input):
        # 1. Create uncommitted changes
        (self.project_dir / "file1.txt").write_text("This is file 1 with mods.")
        (self.project_dir / "new_file.txt").write_text("This is a new file.")

        # 2. Discard changes
        discard_args = MagicMock()
        discard_args.project_dir = self.project_dir
        discard_args.files = []
        discard_args.interactive = False
        discard_args.yes = True

        with self.assertRaises(SystemExit) as cm:
            run_discard(discard_args)
        self.assertEqual(cm.exception.code, 0)

        # 3. Run 'undo' and simulate full restore
        undo_args = MagicMock()
        undo_args.project_dir = self.project_dir

        # Simulate user input:
        # 1. Select the first stash
        # 2. Choose option '5' (Restore entire stash)
        # 3. Confirm the restore ('y')
        mock_input.side_effect = ['1', '5', 'y']

        with self.assertRaises(SystemExit) as cm:
            run_undo(undo_args)
        self.assertEqual(cm.exception.code, 0)

        # 4. Assertions
        # Check that both files were restored
        self.assertEqual((self.project_dir / "file1.txt").read_text(), "This is file 1 with mods.")
        self.assertTrue((self.project_dir / "new_file.txt").exists())
        self.assertEqual((self.project_dir / "new_file.txt").read_text(), "This is a new file.")

        # Check that the stash was dropped
        stash_list_result = subprocess.run(
            [self.git_path, "stash", "list"],
            cwd=self.project_dir, capture_output=True, text=True, check=True
        )
        self.assertNotIn("agent-discard-stash", stash_list_result.stdout)

if __name__ == "__main__":
    unittest.main()
