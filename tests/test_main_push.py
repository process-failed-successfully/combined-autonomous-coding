import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_push

class TestPushCommand(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory and a git repository."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        self.git_path = shutil.which("git")
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create an initial commit
        (self.project_dir / "README.md").write_text("Initial commit")
        subprocess.run([self.git_path, "add", "README.md"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    @patch('shared.git.get_current_branch', return_value='feature-branch')
    @patch('subprocess.run')
    def test_push_success(self, mock_run, mock_get_branch):
        """Test a successful push on a feature branch."""
        # The first call is for 'git status', the second for 'git push'
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # Clean status
            MagicMock(returncode=0)              # Successful push
        ]

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 0)

        # Check that 'git push' was called correctly
        expected_push_cmd = [self.git_path, "-C", str(self.project_dir), "push", "-u", "origin", "feature-branch"]

        # Ensure subprocess.run was called twice
        self.assertEqual(mock_run.call_count, 2)
        # Check the second call was the push command
        actual_cmd = mock_run.call_args_list[1].args[0]
        self.assertEqual(actual_cmd, expected_push_cmd)

    @patch('shared.git.get_current_branch', return_value='feature-branch')
    @patch('subprocess.run')
    def test_push_subprocess_failure(self, mock_run, mock_get_branch):
        """Test that the command handles a git push failure."""
        # The first call is for 'git status', the second for 'git push' which will fail
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # Clean status
            MagicMock(returncode=128)  # Failed push
        ]

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 128)

    def test_push_to_protected_branch_denied(self):
        """Test that pushing to protected branches is denied."""
        for branch in ['main', 'master']:
            with self.subTest(branch=branch):
                # If the branch is 'main', it already exists. Otherwise, create it.
                if branch == 'main':
                    subprocess.run([self.git_path, "checkout", "main"], cwd=self.project_dir, check=True, capture_output=True)
                else:
                    subprocess.run([self.git_path, "checkout", "-b", branch], cwd=self.project_dir, check=True, capture_output=True)

                args = MagicMock()
                args.project_dir = self.project_dir

                with self.assertRaises(SystemExit) as cm:
                    run_push(args)

                self.assertEqual(cm.exception.code, 1)

    def test_push_with_uncommitted_changes(self):
        """Test that pushing with uncommitted changes is denied."""
        # Create an uncommitted change
        (self.project_dir / "README.md").write_text("Uncommitted change")

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 1)

    def test_push_in_non_git_repository(self):
        """Test that the command fails gracefully in a non-git repository."""
        # Create a new directory that is not a git repository
        non_git_dir = Path(tempfile.mkdtemp())

        args = MagicMock()
        args.project_dir = non_git_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 1)

        shutil.rmtree(non_git_dir)

    @patch('subprocess.run')
    @patch('shared.git.get_current_branch', return_value=None)
    def test_push_no_branch_found(self, mock_get_branch, mock_run):
        """Test that the command fails gracefully if the current branch cannot be determined."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)  # Clean status

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_push(args)

        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
