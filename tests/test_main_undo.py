import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import tempfile
import shutil
import os
import sys

from main import run_undo, run_discard

class TestUndoCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.git_path = shutil.which("git")
        if not self.git_path:
            self.fail("Git is not installed or not in PATH")

        # Initialize a git repository
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir, check=True)

        # Create and commit an initial file
        (self.project_dir / "initial_file.txt").write_text("initial content")
        subprocess.run([self.git_path, "add", "initial_file.txt"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_mock_args(self, **kwargs):
        defaults = {
            'project_dir': self.project_dir,
            'files': [],
            'interactive': False,
            'yes': True,
        }
        defaults.update(kwargs)
        return MagicMock(**defaults)

    @patch('builtins.input', return_value='1')
    def test_undo_restores_stashed_changes(self, mock_input):
        # Create a new file and modify an existing one
        (self.project_dir / "new_file.txt").write_text("new file content")
        (self.project_dir / "initial_file.txt").write_text("modified content")

        # Run discard to stash the changes
        discard_args = self._create_mock_args()
        with self.assertRaises(SystemExit) as cm:
            run_discard(discard_args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that the working directory is clean
        status_result = subprocess.run([self.git_path, "status", "--porcelain"], cwd=self.project_dir, capture_output=True, text=True, check=True)
        self.assertEqual(status_result.stdout.strip(), "")

        # Run undo to restore the changes
        undo_args = self._create_mock_args()
        with self.assertRaises(SystemExit) as cm:
            run_undo(undo_args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that the changes have been restored
        self.assertTrue((self.project_dir / "new_file.txt").exists())
        self.assertEqual((self.project_dir / "initial_file.txt").read_text(), "modified content")

        # Verify that the stash is no longer present
        stash_list_result = subprocess.run([self.git_path, "stash", "list"], cwd=self.project_dir, capture_output=True, text=True, check=True)
        self.assertNotIn("agent-discard-stash", stash_list_result.stdout)

if __name__ == '__main__':
    unittest.main()
