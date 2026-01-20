import unittest
from unittest.mock import patch
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys
import io

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import parse_args, run_rollback

class TestRollbackCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create initial commit (No Run ID)
        (self.project_dir / "base.txt").write_text("base content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_rollback_specific_run_id_multiple_commits(self):
        run_id = "run-A"

        # Commit 1 for Run A
        (self.project_dir / "file1.txt").write_text("content 1")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"Add file1\n\nRun ID: {run_id}"], cwd=self.project_dir, check=True)

        # Commit 2 for Run A
        (self.project_dir / "file2.txt").write_text("content 2")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"Add file2\n\nRun ID: {run_id}"], cwd=self.project_dir, check=True)

        # Commit 3 (Run B) - should not be reverted
        (self.project_dir / "file3.txt").write_text("content 3")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Add file3\n\nRun ID: run-B"], cwd=self.project_dir, check=True)

        # Check state before rollback
        self.assertTrue((self.project_dir / "file1.txt").exists())
        self.assertTrue((self.project_dir / "file2.txt").exists())
        self.assertTrue((self.project_dir / "file3.txt").exists())

        # Run Rollback for Run A
        with self.assertRaises(SystemExit) as cm:
            args = parse_args(["rollback", run_id, "--project-dir", str(self.project_dir), "--yes"])
            run_rollback(args)

        self.assertEqual(cm.exception.code, 0)

        # Check state after rollback
        # file1 and file2 should be gone (reverted)
        # file3 should still exist
        self.assertFalse((self.project_dir / "file1.txt").exists(), "file1.txt should have been reverted")
        self.assertFalse((self.project_dir / "file2.txt").exists(), "file2.txt should have been reverted")
        self.assertTrue((self.project_dir / "file3.txt").exists(), "file3.txt should still exist")

    def test_rollback_last_run_default(self):
        run_id = "run-last"
        history_file = self.project_dir / ".agent_history"
        history_file.write_text(f"{run_id}\n")

        # Commit for Last Run
        (self.project_dir / "last.txt").write_text("last content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"Last commit\n\nRun ID: {run_id}"], cwd=self.project_dir, check=True)

        # Run Rollback (defaulting to last)
        with self.assertRaises(SystemExit) as cm:
            args = parse_args(["rollback", "--project-dir", str(self.project_dir), "--yes"])
            run_rollback(args)

        self.assertEqual(cm.exception.code, 0)

        # Check state
        self.assertFalse((self.project_dir / "last.txt").exists())

    def test_rollback_aborts_on_dirty_state(self):
        run_id = "run-dirty"

        # Commit
        (self.project_dir / "file.txt").write_text("clean")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"Clean commit\n\nRun ID: {run_id}"], cwd=self.project_dir, check=True)

        # Make dirty
        (self.project_dir / "file.txt").write_text("dirty")

        stderr_capture = io.StringIO()
        with self.assertRaises(SystemExit) as cm, \
             patch('sys.stderr', stderr_capture):
            args = parse_args(["rollback", run_id, "--project-dir", str(self.project_dir), "--yes"])
            run_rollback(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("uncommitted changes", stderr_capture.getvalue())

if __name__ == '__main__':
    unittest.main()
