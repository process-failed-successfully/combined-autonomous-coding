import unittest
from unittest.mock import patch, MagicMock
import sys
import argparse
from pathlib import Path
import shutil

from main import run_worktrees

class TestWorktreesCreateCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project_worktree")
        # Ensure dir exists for main.py checks
        self.project_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)

        self.args = argparse.Namespace(
            action='create',
            worktree_name='test-worktree',
            branch='test-branch',
            project_dir=self.project_dir,
            force=False,
            yes=True,
        )

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch('main.WorktreeManager')
    @patch('main.shutil.which', return_value='/usr/bin/git')
    def test_create_success_with_branch(self, mock_shutil_which, MockWorktreeManager):
        """Test successful worktree creation with a specific branch."""
        instance = MockWorktreeManager.return_value

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 0)

        MockWorktreeManager.assert_called_with(self.project_dir.resolve())
        instance.create.assert_called_once_with('test-worktree', branch='test-branch')

    @patch('main.WorktreeManager')
    @patch('main.shutil.which', return_value='/usr/bin/git')
    def test_create_success_default_branch(self, mock_shutil_which, MockWorktreeManager):
        """Test successful worktree creation using worktree name as default branch."""
        self.args.branch = None
        instance = MockWorktreeManager.return_value

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 0)

        instance.create.assert_called_once_with('test-worktree', branch='test-worktree')

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('builtins.print')
    def test_create_missing_name(self, mock_print, mock_shutil_which):
        """Test that create fails if worktree_name is not provided."""
        self.args.worktree_name = None
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("❌ Error: 'create' action requires a worktree name.", file=sys.stderr)

    @patch('main.WorktreeManager')
    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('builtins.print')
    def test_create_directory_exists(self, mock_print, mock_shutil_which, MockWorktreeManager):
        """Test that create fails if the worktree directory already exists."""
        instance = MockWorktreeManager.return_value
        instance.create.side_effect = FileExistsError("Worktree path ... already exists.")

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 1)
        # Verify it printed the error
        # Note: main.py prints "❌ Error creating worktree: {e}"
        # So we check if print was called with something containing the error message
        args, _ = mock_print.call_args
        self.assertIn("Error creating worktree", args[0])
        self.assertIn("already exists", args[0])

    @patch('main.WorktreeManager')
    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('builtins.print')
    def test_create_git_failure(self, mock_print, mock_shutil_which, MockWorktreeManager):
        """Test that a failed git command raises error."""
        instance = MockWorktreeManager.return_value
        instance.create.side_effect = Exception("git error")

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 1)
        args, _ = mock_print.call_args
        self.assertIn("Error creating worktree", args[0])
        self.assertIn("git error", args[0])
