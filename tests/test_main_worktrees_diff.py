from main import run_worktrees
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil
import os
import io

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestWorktreesDiff(unittest.TestCase):

    def setUp(self):
        """Set up a temporary git repository and a worktree for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_repo"
        self.project_dir.mkdir()

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create an initial commit
        (self.project_dir / "README.md").write_text("Initial commit")
        subprocess.run(["git", "add", "README.md"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True, capture_output=True)

        # Create a worktree
        self.worktree_name = "test-worktree"
        self.worktrees_base_dir = self.project_dir / "worktrees"
        self.worktree_path = self.worktrees_base_dir / self.worktree_name
        subprocess.run(
            ["git", "worktree", "add", str(self.worktree_path)],
            cwd=self.project_dir, check=True, capture_output=True
        )

    def tearDown(self):
        """Clean up the temporary directory."""
        # On Windows, Git processes can hold onto files, causing shutil.rmtree to fail.
        # Adding a small delay and retries, but the proper fix is more complex (e.g., using psutil to kill processes).
        # For this test suite, we'll try a simple cleanup.
        try:
            # Force remove the worktree from git's internal state first
            subprocess.run(["git", "worktree", "remove", "--force", self.worktree_name], cwd=self.project_dir, capture_output=True)
        except Exception:
            pass  # Ignore errors during cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_worktree_diff_with_changes(self):
        """Test 'worktrees diff' when there are changes in the worktree."""
        # Introduce a change in the worktree
        (self.worktree_path / "README.md").write_text("Modified content")

        args = MagicMock()
        args.action = "diff"
        args.worktree_name = self.worktree_name
        args.project_dir = self.project_dir

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn(f"--- Diff for worktree: {self.worktree_name}", output)
        self.assertIn("--- a/README.md", output)
        self.assertIn("+++ b/README.md", output)
        self.assertIn("-Initial commit", output)
        self.assertIn("+Modified content", output)

    def test_worktree_diff_no_changes(self):
        """Test 'worktrees diff' when there are no changes in the worktree."""
        args = MagicMock()
        args.action = "diff"
        args.worktree_name = self.worktree_name
        args.project_dir = self.project_dir

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn(f"--- Diff for worktree: {self.worktree_name}", output)
        self.assertIn("✅ No changes detected. Worktree is in sync with HEAD.", output)

    def test_worktree_diff_missing_name(self):
        """Test 'worktrees diff' without providing a worktree name."""
        args = MagicMock()
        args.action = "diff"
        args.worktree_name = None
        args.project_dir = self.project_dir

        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("❌ Error: 'diff' action requires a worktree name.", mock_stderr.getvalue())

    def test_worktree_diff_non_existent_worktree(self):
        """Test 'worktrees diff' with a worktree name that does not exist."""
        non_existent_name = "non-existent-worktree"
        args = MagicMock()
        args.action = "diff"
        args.worktree_name = non_existent_name
        args.project_dir = self.project_dir

        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn(f"❌ Error: Worktree '{non_existent_name}' not found", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
