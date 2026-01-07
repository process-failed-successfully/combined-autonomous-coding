import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import run_branch

class TestMainBranch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.branch_file = self.project_dir / ".agent_branch"

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir)
        (self.project_dir / "initial_file.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _get_current_branch(self):
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    @patch('main.sys.exit')
    def test_branch_create(self, mock_exit):
        args = MagicMock()
        args.project_dir = self.project_dir
        args.action = "create"
        args.branch_name = "feature-branch"
        run_branch(args)
        self.assertEqual(self._get_current_branch(), "feature-branch")
        self.assertTrue(self.branch_file.exists())
        self.assertEqual(self.branch_file.read_text().strip(), "feature-branch")

    @patch('main.sys.exit')
    def test_branch_checkout(self, mock_exit):
        subprocess.run(["git", "checkout", "-b", "another-branch"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=self.test_dir, capture_output=True)

        args = MagicMock()
        args.project_dir = self.project_dir
        args.action = "checkout"
        args.branch_name = "another-branch"
        run_branch(args)
        self.assertEqual(self._get_current_branch(), "another-branch")
        self.assertTrue(self.branch_file.exists())
        self.assertEqual(self.branch_file.read_text().strip(), "another-branch")

    @patch('main.sys.exit')
    @patch('builtins.print')
    def test_branch_status(self, mock_print, mock_exit):
        self.branch_file.write_text("status-branch")
        args = MagicMock()
        args.project_dir = self.project_dir
        args.action = "status"
        run_branch(args)
        mock_print.assert_called_with("Agent is currently working on branch: 'status-branch'")

    @patch('main.sys.exit')
    def test_branch_merge(self, mock_exit):
        # Create and checkout feature branch
        subprocess.run(["git", "checkout", "-b", "merge-branch"], cwd=self.test_dir, capture_output=True)
        (self.project_dir / "new_file.txt").write_text("new content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Commit on merge-branch"], cwd=self.test_dir, capture_output=True)
        self.branch_file.write_text("merge-branch")

        args = MagicMock()
        args.project_dir = self.project_dir
        args.action = "merge"
        args.keep_branch = False
        run_branch(args)

        self.assertEqual(self._get_current_branch(), "main")
        self.assertTrue((self.project_dir / "new_file.txt").exists())
        self.assertFalse(self.branch_file.exists())

        # Verify branch was deleted
        result = subprocess.run(["git", "branch", "--list"], cwd=self.test_dir, capture_output=True, text=True)
        self.assertNotIn("merge-branch", result.stdout)

    @patch('main.sys.exit')
    @patch('builtins.print')
    def test_branch_list(self, mock_print, mock_exit):
        subprocess.run(["git", "checkout", "-b", "branch-1"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "branch-2"], cwd=self.test_dir, capture_output=True)
        subprocess.run(["git", "checkout", "main"], cwd=self.test_dir, capture_output=True)
        self.branch_file.write_text("branch-1")

        args = MagicMock()
        args.project_dir = self.project_dir
        args.action = "list"
        run_branch(args)

        # Check that the active agent branch is marked with *
        # and other branches are listed.
        self.assertIn("  * branch-1 (active)", [call[0][0] for call in mock_print.call_args_list])


if __name__ == '__main__':
    unittest.main()
