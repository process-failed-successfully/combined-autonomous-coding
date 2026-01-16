import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import os
import sys

# Add the root of the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_cherry_pick

class TestCherryPickSecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_repo_cherry_pick_security")
        self.test_dir.mkdir(exist_ok=True)

        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)

        # Commit 1
        (self.test_dir / "file1.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=self.test_dir, check=True)

        # Commit with Run ID that could be matched by regex
        (self.test_dir / "file2.txt").write_text("content2")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        # "Run ID: axb"
        subprocess.run(["git", "commit", "-m", "feat: Add file2\n\nRun ID: axb"], cwd=self.test_dir, check=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_cherry_pick_argument_injection(self, mock_stderr, mock_stdout):
        """Test that cherry-pick rejects inputs starting with -"""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = "-p"

        with self.assertRaises(SystemExit) as cm:
            run_cherry_pick(args)

        self.assertEqual(cm.exception.code, 1)
        stderr_output = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
        self.assertIn("Target must be a safe git reference", stderr_output)

    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_run_id_regex_prevention(self, mock_stderr, mock_stdout):
        """Test that Run ID search uses fixed strings, preventing regex matching."""
        args = MagicMock()
        args.project_dir = self.test_dir
        # Searching for "a.b".
        # If treated as regex, "a.b" matches "axb" (which exists).
        # If treated as fixed string, "a.b" does NOT match "axb".
        args.target = "a.b"

        with self.assertRaises(SystemExit) as cm:
            run_cherry_pick(args)

        # We expect it to FAIL to find the commit if fixed strings are used.
        # If it finds it (and exits 0 or proceeds), then regex injection is possible (or accidental matching).
        # run_cherry_pick exits with 1 if not found.
        self.assertEqual(cm.exception.code, 1)

        stderr_output = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
        # It should fail to find it
        self.assertIn("Error: Could not find a git commit for target 'a.b'", stderr_output)

if __name__ == '__main__':
    unittest.main()
