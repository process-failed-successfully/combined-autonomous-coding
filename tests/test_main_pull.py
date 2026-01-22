from main import run_pull
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


class TestPullCommand(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory and a git repository."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize a git repository
        self.git_path = shutil.which("git")
        if not self.git_path:
            self.skipTest("git executable not found")

        subprocess.run([self.git_path, "init", "-b", "main"], check=True, capture_output=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], check=True)

        # Create an initial commit
        (self.project_dir / "README.md").write_text("Initial commit")
        subprocess.run([self.git_path, "add", "README.md"], check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        """Remove the temporary directory and restore CWD."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_pull_success(self, mock_which, mock_run):
        """Test a successful pull in a clean repository."""
        mock_which.return_value = self.git_path
        # Mock 'git status' and 'git pull'
        mock_run.side_effect = [
            MagicMock(stdout=b'', returncode=0),  # Clean status
            MagicMock(returncode=0)               # Successful pull
        ]

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_run.call_count, 2)

        # Check the git pull command
        expected_pull_cmd = [self.git_path, "-C", str(self.project_dir), "pull"]
        mock_run.assert_called_with(expected_pull_cmd, text=True)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_pull_with_uncommitted_changes(self, mock_which, mock_run):
        """Test that pulling with uncommitted changes is denied."""
        mock_which.return_value = self.git_path
        # Simulate uncommitted changes
        mock_run.return_value = MagicMock(stdout=b' M README.md', returncode=0)

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 1)
        # Only 'git status' should be called
        mock_run.assert_called_once()

    @patch('shutil.which', return_value=None)
    def test_pull_no_git_executable(self, mock_which):
        """Test that the command fails if git executable is not found."""
        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 1)

    def test_pull_in_non_git_repository(self):
        """Test that the command fails gracefully in a non-git repository."""
        non_git_dir = Path(tempfile.mkdtemp())

        args = MagicMock()
        args.project_dir = non_git_dir

        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 1)

        shutil.rmtree(non_git_dir)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_pull_subprocess_failure(self, mock_which, mock_run):
        """Test that the command handles a git pull failure."""
        mock_which.return_value = self.git_path
        mock_run.side_effect = [
            MagicMock(stdout=b'', returncode=0),  # Clean status
            MagicMock(returncode=128)             # Failed pull
        ]

        args = MagicMock()
        args.project_dir = self.project_dir

        with self.assertRaises(SystemExit) as cm:
            run_pull(args)

        self.assertEqual(cm.exception.code, 128)
        self.assertEqual(mock_run.call_count, 2)


if __name__ == '__main__':
    unittest.main()
