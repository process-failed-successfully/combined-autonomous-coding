import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os
import subprocess

# Add the root of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.git import is_safe_git_ref, find_commit_by_run_id  # noqa: E402

class TestGitUtils(unittest.TestCase):

    def test_is_safe_git_ref_valid(self):
        """Test valid git references."""
        valid_refs = [
            "master",
            "main",
            "feature/branch",
            "v1.0.0",
            "HEAD",
            "HEAD~1",
            "HEAD^",
            "user@branch",
            "stash@{0}",
            "fix_bug-123",
        ]
        for ref in valid_refs:
            self.assertTrue(is_safe_git_ref(ref), f"Should be valid: {ref}")

    def test_is_safe_git_ref_invalid(self):
        """Test invalid git references."""
        invalid_refs = [
            "-flag",
            "--option",
            "; rm -rf /",
            "branch name",  # spaces not allowed in this strict regex usually
            "| pipe",
            "> redirect",
            "`backtick`",
            "$(command)",
        ]
        for ref in invalid_refs:
            self.assertFalse(is_safe_git_ref(ref), f"Should be invalid: {ref}")

    @patch('shared.git.subprocess.run')
    def test_find_commit_by_run_id_found(self, mock_run):
        """Test finding a commit by Run ID."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "a1b2c3d4e5f6\n"
        mock_run.return_value = mock_result

        project_dir = Path("/tmp/project")
        git_path = "/usr/bin/git"
        run_id = "run-123"

        commit = find_commit_by_run_id(project_dir, git_path, run_id)

        self.assertEqual(commit, "a1b2c3d4e5f6")

        # Verify call arguments
        # It should use --fixed-strings and pass arguments separately
        args, kwargs = mock_run.call_args
        cmd = args[0]

        self.assertIn("--fixed-strings", cmd)
        self.assertIn("Run ID: run-123", cmd)

        # Ensure --grep and value are separate elements if possible,
        # or at least that it's constructed safely.
        # Based on memory: "pass flags and their arguments as separate list items (e.g., ['--grep', val])"
        grep_index = cmd.index("--grep")
        self.assertEqual(cmd[grep_index + 1], "Run ID: run-123")

    @patch('shared.git.subprocess.run')
    def test_find_commit_by_run_id_not_found(self, mock_run):
        """Test when commit is not found."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        project_dir = Path("/tmp/project")
        git_path = "/usr/bin/git"
        run_id = "run-999"

        commit = find_commit_by_run_id(project_dir, git_path, run_id)

        self.assertIsNone(commit)

    @patch('shared.git.subprocess.run')
    def test_find_commit_by_run_id_error(self, mock_run):
        """Test handling of subprocess error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git log")

        project_dir = Path("/tmp/project")
        git_path = "/usr/bin/git"
        run_id = "run-error"

        commit = find_commit_by_run_id(project_dir, git_path, run_id)

        self.assertIsNone(commit)
