import unittest
from unittest.mock import patch, MagicMock
import sys
import argparse
from pathlib import Path
import subprocess
import os
import shutil

from main import run_worktrees

class TestWorktreesCreateCommand(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the project relative to the test file
        self.test_dir = Path(__file__).parent
        self.project_dir = self.test_dir / "test_project_worktree"
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)
        self.worktrees_dir = self.project_dir / "worktrees"
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

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('main.subprocess.run')
    def test_create_success_with_branch(self, mock_subprocess_run, mock_shutil_which):
        """Test successful worktree creation with a specific branch."""
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 0)

        expected_worktree_path = self.worktrees_dir / "test-worktree"
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(self.project_dir), 'worktree', 'add', '-b', 'test-branch', str(expected_worktree_path), 'HEAD'],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('main.subprocess.run')
    def test_create_success_default_branch(self, mock_subprocess_run, mock_shutil_which):
        """Test successful worktree creation using worktree name as default branch."""
        self.args.branch = None
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 0)

        expected_worktree_path = self.worktrees_dir / "test-worktree"
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(self.project_dir), 'worktree', 'add', '-b', 'test-worktree', str(expected_worktree_path), 'HEAD'],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('builtins.print')
    def test_create_missing_name(self, mock_print, mock_shutil_which):
        """Test that create fails if worktree_name is not provided."""
        self.args.worktree_name = None
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("❌ Error: 'create' action requires a worktree name.", file=sys.stderr)

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('builtins.print')
    def test_create_directory_exists(self, mock_print, mock_shutil_which):
        """Test that create fails if the worktree directory already exists."""
        (self.worktrees_dir / "test-worktree").mkdir(parents=True)
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)
        self.assertEqual(cm.exception.code, 1)
        expected_path = self.worktrees_dir / "test-worktree"
        mock_print.assert_any_call(f"❌ Error: Worktree path '{expected_path}' already exists.", file=sys.stderr)

    @patch('main.shutil.which', return_value='/usr/bin/git')
    @patch('main.subprocess.run')
    @patch('main.shutil.rmtree')
    def test_create_git_failure_cleans_up_dir(self, mock_rmtree, mock_subprocess_run, mock_shutil_which):
        """Test that a failed git command cleans up a partially created directory."""
        expected_worktree_path = self.worktrees_dir / "test-worktree"

        def git_fail_side_effect(*args, **kwargs):
            # Simulate git creating the directory before it fails
            expected_worktree_path.mkdir(parents=True, exist_ok=True)
            raise subprocess.CalledProcessError(1, "git", stderr="fatal: some git error")

        mock_subprocess_run.side_effect = git_fail_side_effect

        with self.assertRaises(SystemExit) as cm:
            run_worktrees(self.args)

        self.assertEqual(cm.exception.code, 1)
        mock_rmtree.assert_called_once_with(expected_worktree_path)
