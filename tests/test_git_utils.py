
import unittest
import shutil
import tempfile
import subprocess
from pathlib import Path

# Adjust python path to include project root
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.git import is_safe_git_ref, find_commit_by_run_id  # noqa: E402


class TestGitUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        # Initialize a real git repo for find_commit_by_run_id tests
        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_is_safe_git_ref_valid(self):
        """Test valid git references."""
        valid_refs = [
            "main",
            "feature/new-stuff",
            "v1.0.0",
            "HEAD",
            "HEAD~1",
            "HEAD^",
            "origin/main",
            "7a8b9c",
            "fix_bug_123"
        ]
        for ref in valid_refs:
            with self.subTest(ref=ref):
                self.assertTrue(is_safe_git_ref(ref))

    def test_is_safe_git_ref_invalid(self):
        """Test invalid git references, especially those starting with hyphen."""
        invalid_refs = [
            "-f",
            "--force",
            "-target",
            "",
            " ",
            "; rm -rf /",  # shell injection attempt (though regex limits chars)
            "$(whoami)",
            "| ls"
        ]
        for ref in invalid_refs:
            with self.subTest(ref=ref):
                self.assertFalse(is_safe_git_ref(ref))

    def test_find_commit_by_run_id_found(self):
        """Test finding a commit by Run ID."""
        run_id = "run-12345"
        (self.test_dir / "file.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"feat: Add file\n\nRun ID: {run_id}"], cwd=self.test_dir, check=True)

        commit_hash = find_commit_by_run_id(self.test_dir, run_id)
        self.assertIsNotNone(commit_hash)

        # Verify it's the correct commit
        actual_hash = subprocess.run(
            ["git", "-C", str(self.test_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(commit_hash, actual_hash)

    def test_find_commit_by_run_id_not_found(self):
        """Test finding a commit that doesn't exist."""
        commit_hash = find_commit_by_run_id(self.test_dir, "non-existent-run-id")
        self.assertIsNone(commit_hash)

    def test_find_commit_by_run_id_injection_protection(self):
        """Test that regex injection attempts are handled safely (treated as literal strings)."""
        # This test ensures that special regex chars in run_id are treated literally due to --fixed-strings
        run_id_with_regex = "run-.*"

        # Create a commit with literal text "Run ID: run-.*"
        (self.test_dir / "file2.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"feat: Add file\n\nRun ID: {run_id_with_regex}"], cwd=self.test_dir, check=True)

        # Searching for "run-.*" should find it
        commit_hash = find_commit_by_run_id(self.test_dir, run_id_with_regex)
        self.assertIsNotNone(commit_hash)

        # Let's verify it doesn't match a different run id
        # Create another commit
        run_id_normal = "run-12345"
        (self.test_dir / "file3.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"feat: Another file\n\nRun ID: {run_id_normal}"], cwd=self.test_dir, check=True)

        # Test:
        # Commit has "Run ID: 12345"
        # Search for "12...5"
        # Should return None

        result = find_commit_by_run_id(self.test_dir, "12...5")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
