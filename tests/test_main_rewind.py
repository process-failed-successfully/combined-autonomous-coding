import unittest
from unittest.mock import patch, call
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
from main import parse_args, run_rewind

class TestRewindCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create initial commit
        (self.project_dir / "file1.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)
        self.initial_commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()

        # Create a second commit
        (self.project_dir / "file2.txt").write_text("second file")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add file2.txt"], cwd=self.project_dir, check=True)
        self.second_commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()

        # Create a third commit
        (self.project_dir / "file1.txt").write_text("updated content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Update file1.txt"], cwd=self.project_dir, check=True)
        self.third_commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_rewind_to_specific_commit(self):
        with self.assertRaises(SystemExit) as cm:
            args = parse_args(["rewind", self.second_commit_hash, "--project-dir", str(self.project_dir), "--yes"])
            run_rewind(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.project_dir / "file2.txt").exists())
        self.assertEqual((self.project_dir / "file1.txt").read_text(), "initial content")

        current_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()
        self.assertEqual(current_hash, self.second_commit_hash)

    def test_rewind_relative_commit(self):
        with self.assertRaises(SystemExit) as cm:
            args = parse_args(["rewind", "HEAD~1", "--project-dir", str(self.project_dir), "--yes"])
            run_rewind(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.project_dir / "file2.txt").exists())
        self.assertEqual((self.project_dir / "file1.txt").read_text(), "initial content")

        current_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()
        self.assertEqual(current_hash, self.second_commit_hash)

    def test_rewind_aborts_with_uncommitted_changes(self):
        # 1. Create an untracked file
        (self.project_dir / "new_untracked_file.txt").write_text("uncommitted change")
        # 2. Modify a tracked file
        (self.project_dir / "file1.txt").write_text("new uncommitted content")

        stderr_capture = io.StringIO()
        with self.assertRaises(SystemExit) as cm, \
             unittest.mock.patch('sys.stderr', stderr_capture):
            args = parse_args(["rewind", self.initial_commit_hash, "--project-dir", str(self.project_dir), "--yes"])
            run_rewind(args)

        self.assertEqual(cm.exception.code, 1)
        output = stderr_capture.getvalue()
        self.assertIn("Your repository has uncommitted changes", output)
        self.assertIn("Please commit or stash them before using rewind.", output)

        # Verify no changes were made
        current_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()
        self.assertEqual(current_hash, self.third_commit_hash)
        self.assertTrue((self.project_dir / "new_untracked_file.txt").exists())
        self.assertEqual((self.project_dir / "file1.txt").read_text(), "new uncommitted content")

    @patch('builtins.input', side_effect=['2', 'y'])
    def test_rewind_interactive_mode(self, mock_input):
        with self.assertRaises(SystemExit) as cm:
            args = parse_args(["rewind", "--project-dir", str(self.project_dir)])
            run_rewind(args)

        self.assertEqual(cm.exception.code, 0)

        # Interactive mode selects the second commit from the list (which is the second commit)
        current_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()

        # The list is in reverse chronological order, so entry 2 is the second commit
        # third commit is [1]
        # second commit is [2]
        self.assertEqual(current_hash, self.second_commit_hash)

    def test_rewind_by_run_id(self):
        # Create a fourth commit with a Run ID in the message
        run_id = "gemini_agent_test_project_12345678"
        commit_message = f"Feature: Add user authentication\n\nRun ID: {run_id}"
        (self.project_dir / "file3.txt").write_text("user auth file")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=self.project_dir, check=True)
        fourth_commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()

        # Create a fifth commit on top
        (self.project_dir / "file4.txt").write_text("another file")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add file4.txt"], cwd=self.project_dir, check=True)

        # Now, rewind to the Run ID
        with self.assertRaises(SystemExit) as cm:
            args = parse_args(["rewind", run_id, "--project-dir", str(self.project_dir), "--yes"])
            run_rewind(args)

        self.assertEqual(cm.exception.code, 0)

        # Check that the HEAD is now at the fourth commit
        current_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()
        self.assertEqual(current_hash, fourth_commit_hash)

        # Check the file state
        self.assertTrue((self.project_dir / "file3.txt").exists())
        self.assertFalse((self.project_dir / "file4.txt").exists())

if __name__ == '__main__':
    unittest.main()
