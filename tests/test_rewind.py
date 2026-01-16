import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import os
import sys

# Add the root of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_rewind

class TestRewindCommand(unittest.TestCase):
    def setUp(self):
        """Set up a temporary git repository for testing."""
        self.test_dir = Path("test_repo_rewind")
        self.test_dir.mkdir(exist_ok=True)

        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)

        # Create the first commit
        (self.test_dir / "file1.txt").write_text("Initial content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, check=True)
        self.initial_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.test_dir, check=True, capture_output=True, text=True
        ).stdout.strip()

        # Create a second commit
        (self.test_dir / "file2.txt").write_text("Second commit content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        run_id = "run-67890"
        subprocess.run(["git", "commit", "-m", f"feat: Add file2\n\nRun ID: {run_id}"], cwd=self.test_dir, check=True)

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    @patch('builtins.input', side_effect=['y'])
    def test_rewind_successful(self, mock_input):
        """Test a successful rewind operation."""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = self.initial_commit
        args.yes = True

        with self.assertRaises(SystemExit) as cm:
            run_rewind(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse((self.test_dir / "file2.txt").exists())

    @patch('sys.stderr')
    def test_rewind_unsafe_ref(self, mock_stderr):
        """Test that an unsafe git reference is rejected."""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = "; rm -rf /"
        args.yes = True

        with self.assertRaises(SystemExit) as cm:
            run_rewind(args)

        self.assertEqual(cm.exception.code, 1)
        stderr_output = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
        self.assertIn("Invalid or unsafe git reference", stderr_output)

if __name__ == '__main__':
    unittest.main()
