import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import shutil
import subprocess
import os
import sys

# Add the root of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # noqa: E402

from shared.git import is_safe_git_ref, find_commit_by_run_id

class TestGitUtils(unittest.TestCase):
    def test_is_safe_git_ref(self):
        """Test is_safe_git_ref with various inputs."""
        # Valid inputs
        self.assertTrue(is_safe_git_ref("main"))
        self.assertTrue(is_safe_git_ref("feature/branch"))
        self.assertTrue(is_safe_git_ref("v1.0.0"))
        self.assertTrue(is_safe_git_ref("a1b2c3d"))
        self.assertTrue(is_safe_git_ref("stash@{0}"))
        self.assertTrue(is_safe_git_ref("refs/heads/main"))
        self.assertTrue(is_safe_git_ref("HEAD~1"))
        self.assertTrue(is_safe_git_ref("master^"))
        self.assertTrue(is_safe_git_ref("feature/branch^2"))

        # Invalid inputs
        self.assertFalse(is_safe_git_ref("-flag"))
        self.assertFalse(is_safe_git_ref("--option"))
        self.assertFalse(is_safe_git_ref("rm -rf /"))
        self.assertFalse(is_safe_git_ref("branch; rm -rf /"))
        self.assertFalse(is_safe_git_ref("branch && command"))
        self.assertFalse(is_safe_git_ref("branch|command"))
        self.assertFalse(is_safe_git_ref(""))
        self.assertFalse(is_safe_git_ref(None))

    def test_find_commit_by_run_id(self):
        """Test finding a commit by Run ID."""
        # Create a temp repo
        test_dir = Path(tempfile.mkdtemp())
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=test_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=test_dir, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=test_dir, check=True)

            # Create a commit without Run ID
            (test_dir / "file1.txt").write_text("content")
            subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=test_dir, check=True)

            # Create a commit with Run ID
            run_id = "run-12345"
            (test_dir / "file2.txt").write_text("content2")
            subprocess.run(["git", "add", "."], cwd=test_dir, check=True)
            subprocess.run(["git", "commit", "-m", f"feat: something\n\nRun ID: {run_id}"], cwd=test_dir, check=True)

            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=test_dir, check=True, capture_output=True, text=True
            ).stdout.strip()

            git_path = shutil.which("git")

            # Test finding existing Run ID
            found_hash = find_commit_by_run_id(test_dir, git_path, run_id)
            self.assertEqual(found_hash, commit_hash)

            # Test finding non-existent Run ID
            self.assertIsNone(find_commit_by_run_id(test_dir, git_path, "run-99999"))

            # Test with invalid project dir
            self.assertIsNone(find_commit_by_run_id(Path("/non/existent"), git_path, run_id))

        finally:
            shutil.rmtree(test_dir)

if __name__ == '__main__':
    unittest.main()
