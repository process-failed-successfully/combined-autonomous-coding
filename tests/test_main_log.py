from main import _run_log_logic
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys
import io
from contextlib import redirect_stderr

# Add the parent directory to the sys.path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestMainLog(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=self.test_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)

        # Create some commits
        (self.project_dir / "file1.txt").write_text("content1")
        subprocess.run(["git", "add", "file1.txt"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, check=True)

        (self.project_dir / "file2.txt").write_text("content2")
        subprocess.run(["git", "add", "file2.txt"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=self.test_dir, check=True)

        (self.project_dir / "file3.txt").write_text("content3")
        subprocess.run(["git", "add", "file3.txt"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Third commit"], cwd=self.test_dir, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.subprocess.run')
    def test_log_success(self, mock_subprocess_run):
        """Test that the log command runs successfully and calls git log."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process

        result = _run_log_logic(project_dir=self.project_dir)

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once()

        called_command = mock_subprocess_run.call_args[0][0]
        self.assertIn("log", called_command)

    @patch('main.subprocess.run')
    def test_log_with_count(self, mock_subprocess_run):
        """Test that the --count argument is correctly passed to git log."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process

        result = _run_log_logic(project_dir=self.project_dir, count=2)

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once()

        called_command = mock_subprocess_run.call_args[0][0]
        self.assertIn("-n", called_command)
        self.assertIn("2", called_command)

    def test_log_no_git_repo(self):
        """Test that the log command fails gracefully in a non-git directory."""
        non_git_dir = Path(tempfile.mkdtemp())

        f = io.StringIO()
        with redirect_stderr(f):
            result = _run_log_logic(project_dir=non_git_dir)

        self.assertFalse(result)
        output = f.getvalue()
        self.assertIn("Not a git repository", output)

        shutil.rmtree(non_git_dir)


if __name__ == '__main__':
    unittest.main()
