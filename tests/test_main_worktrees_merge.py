import unittest
import subprocess
from pathlib import Path
import tempfile
import shutil
import os

from main import run_worktrees


class TestWorktreeMerge(unittest.TestCase):
    def setUp(self):
        self.repo_dir = Path(tempfile.mkdtemp())
        self.worktrees_dir = self.repo_dir / "worktrees"
        self.worktree_name = "test-worktree"
        self.worktree_path = self.worktrees_dir / self.worktree_name

        # Git environment variables
        self.env = os.environ.copy()
        self.env["GIT_AUTHOR_NAME"] = "Test User"
        self.env["GIT_AUTHOR_EMAIL"] = "test@example.com"
        self.env["GIT_COMMITTER_NAME"] = "Test User"
        self.env["GIT_COMMITTER_EMAIL"] = "test@example.com"

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, env=self.env)
        (self.repo_dir / "README.md").write_text("Initial commit")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True, env=self.env)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_dir, check=True, env=self.env)

        # Create a worktree
        self.worktrees_dir.mkdir()
        subprocess.run(
            ["git", "worktree", "add", "-b", self.worktree_name, str(self.worktree_path)],
            cwd=self.repo_dir,
            check=True,
            env=self.env
        )

        # Create a new file in the worktree
        (self.worktree_path / "new_feature.txt").write_text("This is a new feature.")

    def tearDown(self):
        shutil.rmtree(self.repo_dir)

    def test_merge_worktree(self):
        """Tests the worktree merge functionality without cleaning up."""
        args = type("Args", (), {
            "action": "merge",
            "worktree_name": self.worktree_name,
            "project_dir": self.repo_dir,
            "clean": False,
            "yes": True,
        })()

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify the merge commit on the main branch
        log_output = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
            env=self.env
        ).stdout
        self.assertIn(f"Merge branch '{self.worktree_name}'", log_output)
        self.assertIn("Autocommit: Worktree merge", log_output)

        # Verify the new file exists in the main repo
        self.assertTrue((self.repo_dir / "new_feature.txt").exists())

        # Verify worktree and branch are not removed
        self.assertTrue(self.worktree_path.exists())
        branch_output = subprocess.run(
            ["git", "branch"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
            env=self.env
        ).stdout
        self.assertIn(self.worktree_name, branch_output)

    def test_merge_worktree_with_clean(self):
        """Tests the worktree merge functionality with the --clean flag."""
        args = type("Args", (), {
            "action": "merge",
            "worktree_name": self.worktree_name,
            "project_dir": self.repo_dir,
            "clean": True,
            "yes": True,
        })()

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify the merge commit on the main branch
        log_output = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
            env=self.env
        ).stdout
        self.assertIn(f"Merge branch '{self.worktree_name}'", log_output)

        # Verify the new file exists in the main repo
        self.assertTrue((self.repo_dir / "new_feature.txt").exists())

        # Verify worktree and branch are removed
        self.assertFalse(self.worktree_path.exists())
        branch_output = subprocess.run(
            ["git", "branch"],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
            text=True,
            env=self.env
        ).stdout
        self.assertNotIn(self.worktree_name, branch_output)


if __name__ == "__main__":
    unittest.main()
