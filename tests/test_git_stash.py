import unittest
import shutil
import tempfile
import subprocess
from pathlib import Path
from shared.git import (
    run_git,
    get_git_stash_list,
    push_stash,
    pop_stash,
    apply_stash,
    drop_stash,
    get_stash_show
)

class TestGitStash(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Initialize repo
        subprocess.run(["git", "init"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)

        # Create initial commit
        (self.project_dir / "file.txt").write_text("Initial content")
        run_git(["add", "."], self.project_dir)
        run_git(["commit", "-m", "Initial commit"], self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_push_and_list_stash(self):
        # Modify file
        (self.project_dir / "file.txt").write_text("Modified content")

        # Push stash
        success = push_stash(self.project_dir, "Test Stash")
        self.assertTrue(success)

        # Verify content reverted (stash push resets to HEAD by default if no pathspec)
        # Wait, git stash push does reset.
        self.assertEqual((self.project_dir / "file.txt").read_text(), "Initial content")

        # List stashes
        stashes = get_git_stash_list(self.project_dir)
        self.assertEqual(len(stashes), 1)
        self.assertEqual(stashes[0]["index"], 0)
        self.assertIn("Test Stash", stashes[0]["message"])

    def test_apply_stash(self):
        (self.project_dir / "file.txt").write_text("Modified content")
        push_stash(self.project_dir, "Stash 1")

        # Apply
        success = apply_stash(self.project_dir, 0)
        self.assertTrue(success)
        self.assertEqual((self.project_dir / "file.txt").read_text(), "Modified content")

        # Ensure stash still exists
        stashes = get_git_stash_list(self.project_dir)
        self.assertEqual(len(stashes), 1)

    def test_pop_stash(self):
        (self.project_dir / "file.txt").write_text("Modified content")
        push_stash(self.project_dir, "Stash 1")

        # Pop
        success = pop_stash(self.project_dir, 0)
        self.assertTrue(success)
        self.assertEqual((self.project_dir / "file.txt").read_text(), "Modified content")

        # Ensure stash is gone
        stashes = get_git_stash_list(self.project_dir)
        self.assertEqual(len(stashes), 0)

    def test_drop_stash(self):
        (self.project_dir / "file.txt").write_text("Modified content")
        push_stash(self.project_dir, "Stash 1")

        # Drop
        success = drop_stash(self.project_dir, 0)
        self.assertTrue(success)

        # Ensure stash is gone
        stashes = get_git_stash_list(self.project_dir)
        self.assertEqual(len(stashes), 0)

        # Content should remain initial (since we dropped, not popped)
        self.assertEqual((self.project_dir / "file.txt").read_text(), "Initial content")

    def test_stash_show(self):
        (self.project_dir / "file.txt").write_text("Modified content")
        push_stash(self.project_dir, "Stash 1")

        diff = get_stash_show(self.project_dir, 0)
        self.assertIn("diff --git a/file.txt b/file.txt", diff)
        self.assertIn("+Modified content", diff)

    def test_stash_untracked(self):
        (self.project_dir / "new_file.txt").write_text("New content")

        # Push with include_untracked=True
        success = push_stash(self.project_dir, "Stash Untracked", include_untracked=True)
        self.assertTrue(success)

        # File should be gone
        self.assertFalse((self.project_dir / "new_file.txt").exists())

        # Pop
        pop_stash(self.project_dir, 0)
        self.assertTrue((self.project_dir / "new_file.txt").exists())

if __name__ == "__main__":
    unittest.main()
