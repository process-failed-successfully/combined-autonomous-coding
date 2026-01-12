
import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import sys
import os

# Adjust the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_git

import tempfile
class TestMainGitCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        (self.project_dir / ".git").mkdir(exist_ok=True)

        # Create a mock worktree directory
        self.worktree_path = self.project_dir / "worktrees" / "sprint-task-123"
        self.worktree_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('main.shutil.which')
    @patch('main.subprocess.run')
    def test_run_git_success(self, mock_subprocess_run, mock_shutil_which):
        # Mock that the 'git' executable is found
        mock_shutil_which.return_value = '/usr/bin/git'

        # Configure the mock for subprocess.run
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Git status output"
        mock_process.stderr = ""
        mock_subprocess_run.return_value = mock_process

        # Create a mock args object
        args = argparse.Namespace(
            project_dir=self.project_dir,
            task='123',
            git_args=['status']
        )

        # Run the function and assert it exits with 0
        with self.assertRaises(SystemExit) as cm:
            run_git(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that subprocess.run was called correctly
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', 'status'],
            cwd=self.worktree_path,
            capture_output=True,
            text=True
        )

    @patch('main.shutil.which')
    def test_run_git_no_git_executable(self, mock_shutil_which):
        # Mock that 'git' is not found
        mock_shutil_which.return_value = None

        args = argparse.Namespace(
            project_dir=self.project_dir,
            task='123',
            git_args=['status']
        )

        with self.assertRaises(SystemExit) as cm:
            run_git(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.shutil.which')
    def test_run_git_worktree_not_found(self, mock_shutil_which):
        mock_shutil_which.return_value = '/usr/bin/git'

        args = argparse.Namespace(
            project_dir=self.project_dir,
            task='nonexistent-task',
            git_args=['status']
        )

        with self.assertRaises(SystemExit) as cm:
            run_git(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.shutil.which')
    def test_run_git_no_task_id(self, mock_shutil_which):
        mock_shutil_which.return_value = '/usr/bin/git'
        args = argparse.Namespace(
            project_dir=self.project_dir,
            task=None,
            git_args=['status']
        )
        with self.assertRaises(SystemExit) as cm:
            run_git(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.shutil.which')
    def test_run_git_no_git_args(self, mock_shutil_which):
        mock_shutil_which.return_value = '/usr/bin/git'
        args = argparse.Namespace(
            project_dir=self.project_dir,
            task='123',
            git_args=[]
        )
        with self.assertRaises(SystemExit) as cm:
            run_git(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.shutil.which')
    @patch('main.subprocess.run')
    def test_run_git_command_failure(self, mock_subprocess_run, mock_shutil_which):
        mock_shutil_which.return_value = '/usr/bin/git'
        mock_process = MagicMock()
        mock_process.returncode = 128
        mock_process.stdout = ""
        mock_process.stderr = "fatal: not a git repository"
        mock_subprocess_run.return_value = mock_process

        args = argparse.Namespace(
            project_dir=self.project_dir,
            task='123',
            git_args=['invalid-command']
        )

        with self.assertRaises(SystemExit) as cm:
            run_git(args)
        self.assertEqual(cm.exception.code, 128)

        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', 'invalid-command'],
            cwd=self.worktree_path,
            capture_output=True,
            text=True
        )

if __name__ == '__main__':
    unittest.main()
