import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import subprocess
import shutil
# We need to make sure we can import shared
import sys
import os
sys.path.append(os.getcwd())

from shared.worktree import WorktreeManager

class TestWorktreeManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/project")
        self.manager = WorktreeManager(self.project_dir)

    @patch("shared.worktree.subprocess.run")
    @patch("shared.worktree.shutil.which")
    def test_list_worktrees(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/git"

        # Mock git output
        stdout = """worktree /tmp/project
HEAD 123456
branch refs/heads/main

worktree /tmp/project/worktrees/wt1
HEAD 789012
branch refs/heads/wt1
"""
        mock_run.return_value = MagicMock(stdout=stdout, returncode=0)

        worktrees = self.manager.list_worktrees()

        # Should only return wt1 because it is in worktrees/ dir
        self.assertEqual(len(worktrees), 1)
        self.assertEqual(worktrees[0]["name"], "wt1")
        self.assertEqual(worktrees[0]["branch"], "refs/heads/wt1")

    @patch("shared.worktree.subprocess.run")
    def test_create(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        # We need to mock path exists/mkdir logic inside create
        # But create calls ensure_worktrees_dir which calls mkdir on Path
        # And it checks if path exists.

        with patch("pathlib.Path.exists", return_value=False), \
             patch("pathlib.Path.mkdir") as mock_mkdir:

            success = self.manager.create("new-feature")
            self.assertTrue(success)
            mock_run.assert_called()
            args = mock_run.call_args[0][0]
            self.assertIn("worktree", args)
            self.assertIn("add", args)
            # path string will be /tmp/project/worktrees/new-feature
            # check if new-feature is in the args as part of path
            self.assertTrue(any("new-feature" in str(a) for a in args))

    @patch("shared.worktree.subprocess.run")
    def test_remove(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        with patch("pathlib.Path.exists", return_value=True), \
             patch("shutil.rmtree") as mock_rmtree:

             success = self.manager.remove("wt1")
             self.assertTrue(success)
             mock_run.assert_called()
             # Should remove dir
             mock_rmtree.assert_called()

    @patch("shared.worktree.subprocess.run")
    def test_get_status(self, mock_run):
        mock_run.return_value = MagicMock(stdout=" M file.py\n", returncode=0)
        with patch("pathlib.Path.exists", return_value=True):
            status = self.manager.get_status("wt1")
            self.assertEqual(status, " M file.py\n")

    @patch("shared.worktree.subprocess.run")
    def test_diff(self, mock_run):
        mock_run.return_value = MagicMock(stdout="diff content", returncode=0)
        with patch("pathlib.Path.exists", return_value=True):
            diff = self.manager.diff("wt1")
            self.assertEqual(diff, "diff content")

if __name__ == "__main__":
    unittest.main()
