
import unittest
import shutil
import subprocess
from pathlib import Path
import tempfile
import os
from agents.shared.worktree_manager import WorktreeManager

class TestWorktreeManager(unittest.TestCase):
    def setUp(self):
        # Set Git identity for tests to avoid failures in CI environments
        os.environ["GIT_AUTHOR_NAME"] = "Test User"
        os.environ["GIT_AUTHOR_EMAIL"] = "test@example.com"
        os.environ["GIT_COMMITTER_NAME"] = "Test User"
        os.environ["GIT_COMMITTER_EMAIL"] = "test@example.com"

        self.tmp_dir = tempfile.mkdtemp(prefix="test_worktree_repo_")
        self.repo_dir = Path(self.tmp_dir)
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize a real git repo
        subprocess.run(["git", "init"], cwd=self.repo_dir, check=True)
        # Create a commit so we have HEAD
        (self.repo_dir / "README.md").write_text("initial")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=self.repo_dir, check=True)
        
        self.manager = WorktreeManager(self.repo_dir)

    def tearDown(self):
        # Allow cleanup of read-only files if needed
        if hasattr(self, "tmp_dir") and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_create_worktree(self):
        wt_path = self.manager.create_worktree("t1")
        self.assertTrue(wt_path.exists())
        self.assertTrue((wt_path / ".git").exists())
        self.assertTrue((wt_path / "README.md").exists())
        
        # Verify it's on a new branch
        res = subprocess.run(["git", "branch", "--show-current"], cwd=wt_path, capture_output=True, text=True)
        self.assertEqual(res.stdout.strip(), "sprint/task-t1")

    def test_merge_worktree_success(self):
        wt_path = self.manager.create_worktree("t2")
        
        # Make changes in worktree
        (wt_path / "new_file.txt").write_text("hello")
        subprocess.run(["git", "add", "new_file.txt"], cwd=wt_path, check=True)
        subprocess.run(["git", "commit", "-m", "add file"], cwd=wt_path, check=True)
        
        # Merge
        success = self.manager.merge_worktree("t2")
        self.assertTrue(success)
        
        # Verify changes in main repo
        self.assertTrue((self.repo_dir / "new_file.txt").exists())

    def test_rescue_worktree(self):
        wt_path = self.manager.create_worktree("t_rescue")
        (wt_path / "wip_file.txt").write_text("WIP")
        
        # Rescue
        res = self.manager.rescue_worktree("t_rescue")
        self.assertTrue(res)
        
        # Verify commit exists on branch
        # (Git commit would have happened in worktree)
        # Check if file is tracked in the branch now
        res = subprocess.run(["git", "show", "sprint/task-t_rescue:wip_file.txt"], cwd=self.repo_dir, capture_output=True, text=True)
        self.assertEqual(res.stdout.strip(), "WIP")

    def test_cleanup_preserve_branch(self):
        wt_path = self.manager.create_worktree("t_preserve")
        self.manager.cleanup_worktree("t_preserve", delete_branch=False)
        self.assertFalse(wt_path.exists())
        
        # Branch should still exist
        res = subprocess.run(["git", "branch", "--list", "sprint/task-t_preserve"], cwd=self.repo_dir, capture_output=True, text=True)
        self.assertIn("sprint/task-t_preserve", res.stdout)
        
        # Cleanup properly for next tests
        subprocess.run(["git", "branch", "-D", "sprint/task-t_preserve"], cwd=self.repo_dir)

    def test_cleanup_worktree(self):
        wt_path = self.manager.create_worktree("t3")
        self.assertTrue(wt_path.exists())
        
        self.manager.cleanup_worktree("t3")
        self.assertFalse(wt_path.exists())
        
        # Verify branch deleted
        res = subprocess.run(["git", "branch", "--list", "sprint/task-t3"], cwd=self.repo_dir, capture_output=True, text=True)
        self.assertEqual(res.stdout.strip(), "")

if __name__ == "__main__":
    unittest.main()
