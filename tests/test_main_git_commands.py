import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil
import os
from argparse import Namespace

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_push, run_pull

class TestMainGitCommands(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir)
        (self.project_dir / "test.txt").write_text("initial commit")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main._git_pre_flight_checks')
    @patch('shared.git.get_current_branch')
    @patch('subprocess.run')
    def test_run_push_success(self, mock_subprocess_run, mock_get_current_branch, mock_pre_flight_checks):
        mock_pre_flight_checks.return_value = '/usr/bin/git'
        mock_get_current_branch.return_value = 'feature-branch'
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 0)
        mock_pre_flight_checks.assert_called_once_with(self.project_dir)
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(self.project_dir), 'push', '-u', 'origin', 'feature-branch'],
            text=True
        )

    @patch('main._git_pre_flight_checks')
    def test_run_push_dirty_workdir(self, mock_pre_flight_checks):
        mock_pre_flight_checks.side_effect = SystemExit(1)

        args = Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('main._git_pre_flight_checks')
    @patch('shared.git.get_current_branch')
    def test_run_push_protected_branch(self, mock_get_current_branch, mock_pre_flight_checks):
        mock_pre_flight_checks.return_value = '/usr/bin/git'
        mock_get_current_branch.return_value = 'main'

        args = Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('main._git_pre_flight_checks')
    def test_run_push_no_git(self, mock_pre_flight_checks):
        mock_pre_flight_checks.side_effect = SystemExit(1)

        args = Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('main._git_pre_flight_checks')
    @patch('subprocess.run')
    def test_run_pull_success(self, mock_subprocess_run, mock_pre_flight_checks):
        mock_pre_flight_checks.return_value = '/usr/bin/git'
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        args = Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 0)
        mock_pre_flight_checks.assert_called_once_with(self.project_dir)
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(self.project_dir), 'pull'],
            text=True
        )

    @patch('main._git_pre_flight_checks')
    def test_run_pull_dirty_workdir(self, mock_pre_flight_checks):
        mock_pre_flight_checks.side_effect = SystemExit(1)

        args = Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
