import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Adjust the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_push

class TestMainPush(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True, capture_output=True)
        (self.project_dir / "test.txt").write_text("initial commit")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_push_feature_branch_success(self, mock_subprocess_run):
        subprocess.run(["git", "checkout", "-b", "feature/test-branch"], cwd=self.project_dir, check=True, capture_output=True)
        args = MagicMock()
        args.project_dir = self.project_dir

        mock_subprocess_run.side_effect = [
            MagicMock(stdout="feature/test-branch\n", returncode=0), # git rev-parse
            MagicMock(returncode=0) # git push
        ]

        with self.assertRaises(SystemExit) as cm:
            run_push(args)
        self.assertEqual(cm.exception.code, 0)

    @patch('builtins.print')
    def test_push_on_main_branch_fails(self, mock_print):
        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.print')
    def test_push_on_master_branch_fails(self, mock_print):
        subprocess.run(["git", "checkout", "-b", "master"], cwd=self.project_dir, check=True, capture_output=True)
        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.print')
    def test_push_in_non_git_repo_fails(self, mock_print):
        non_git_dir = Path(tempfile.mkdtemp())
        args = MagicMock()
        args.project_dir = non_git_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)
        self.assertEqual(cm.exception.code, 1)
        shutil.rmtree(non_git_dir)

    @patch('subprocess.run')
    def test_push_subprocess_failure(self, mock_subprocess_run):
        subprocess.run(["git", "checkout", "-b", "feature/another-branch"], cwd=self.project_dir, check=True, capture_output=True)
        args = MagicMock()
        args.project_dir = self.project_dir

        mock_subprocess_run.side_effect = [
            MagicMock(stdout="feature/another-branch\n", returncode=0), # git rev-parse
            MagicMock(returncode=128, stderr="remote error: permission denied") # git push
        ]

        with self.assertRaises(SystemExit) as cm:
            run_push(args)
        self.assertEqual(cm.exception.code, 128)
