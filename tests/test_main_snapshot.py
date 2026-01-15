import unittest
from unittest.mock import patch
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import io
import contextlib

# Make sure the main script can be imported
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main

class TestSnapshotCommand(unittest.TestCase):
    def setUp(self):
        """Set up a temporary project directory with a git repository."""
        self.test_dir = Path("test_project_snapshot")
        # Clean up from previous runs if any
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)

        # Initialize Git repo
        subprocess.run(["git", "init"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, capture_output=True)

        # Create some files
        (self.test_dir / "file1.txt").write_text("hello")
        (self.test_dir / "feature_list.json").write_text('{"features": []}')
        (self.test_dir / "app_spec.txt").write_text('test spec')
        subprocess.run(["git", "add", "."], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, capture_output=True)

        self.archive_dir = self.test_dir / ".agent_archives"


    def tearDown(self):
        """Clean up the temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_snapshot_create_and_list(self):
        """Test creating a snapshot and then listing it."""
        # --- Create Snapshot ---
        # Note: 'name' is positional, so we don't provide it here to get a timestamped one.
        args = main.parse_args(["snapshot", "create", "--project-dir", str(self.test_dir), "--yes"])

        with self.assertRaises(SystemExit) as cm:
            main.run_snapshot(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify snapshot directory and tag
        self.assertTrue(self.archive_dir.exists())
        snapshot_dirs = list(self.archive_dir.iterdir())
        self.assertEqual(len(snapshot_dirs), 1)
        snapshot_dir = snapshot_dirs[0]
        self.assertTrue(snapshot_dir.name.startswith("snapshot-"))

        # Verify tag
        tag_name = f"snapshot/{snapshot_dir.name}"
        result = subprocess.run(["git", "tag"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertIn(tag_name, result.stdout)

        # Verify artifacts
        self.assertTrue((snapshot_dir / "feature_list.json").exists())

        # --- List Snapshot ---
        args_list = main.parse_args(["snapshot", "list", "--project-dir", str(self.test_dir)])

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm_list:
                main.run_snapshot(args_list)

        self.assertEqual(cm_list.exception.code, 0)
        output = f.getvalue()
        self.assertIn(snapshot_dir.name, output)
        self.assertIn("✅ Tagged", output)

    def test_snapshot_restore(self):
        """Test restoring a snapshot."""
        snapshot_name = "test-snapshot-restore"
        # Correctly pass snapshot name as a positional argument
        args_create = main.parse_args(["snapshot", "create", snapshot_name, "--project-dir", str(self.test_dir), "--yes"])
        with self.assertRaises(SystemExit):
            main.run_snapshot(args_create)

        # Modify the project state
        (self.test_dir / "feature_list.json").unlink()
        (self.test_dir / "new_file.txt").write_text("new content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Second commit (deleted feature_list)"], cwd=self.test_dir, capture_output=True)

        self.assertFalse((self.test_dir / "feature_list.json").exists())

        # --- Restore Snapshot ---
        args_restore = main.parse_args(["snapshot", "restore", snapshot_name, "--project-dir", str(self.test_dir), "--yes"])
        with self.assertRaises(SystemExit) as cm:
            main.run_snapshot(args_restore)
        self.assertEqual(cm.exception.code, 0)

        # Verify restored artifacts
        self.assertTrue((self.test_dir / "feature_list.json").exists())

        # Verify git state (should be at the first commit)
        result = subprocess.run(["git", "log", "-1", "--oneline"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertIn("Initial commit", result.stdout)
        self.assertNotIn("Second commit", result.stdout)

        # Verify detached head state
        result_status = subprocess.run(["git", "status"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertIn("HEAD detached at", result_status.stdout)

    def test_snapshot_delete(self):
        """Test deleting a snapshot."""
        snapshot_name = "test-snapshot-delete"
        # Create a snapshot
        # Correctly pass snapshot name as a positional argument
        args_create = main.parse_args(["snapshot", "create", snapshot_name, "--project-dir", str(self.test_dir), "--yes"])
        with self.assertRaises(SystemExit):
            main.run_snapshot(args_create)

        snapshot_dir = self.archive_dir / snapshot_name
        tag_name = f"snapshot/{snapshot_name}"

        self.assertTrue(snapshot_dir.exists())
        result = subprocess.run(["git", "tag"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertIn(tag_name, result.stdout)

        # --- Delete Snapshot ---
        args_delete = main.parse_args(["snapshot", "delete", snapshot_name, "--project-dir", str(self.test_dir), "--yes"])
        with self.assertRaises(SystemExit) as cm:
            main.run_snapshot(args_delete)
        self.assertEqual(cm.exception.code, 0)

        # Verify deletion
        self.assertFalse(snapshot_dir.exists())
        result = subprocess.run(["git", "tag"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertNotIn(tag_name, result.stdout)

if __name__ == '__main__':
    unittest.main()
