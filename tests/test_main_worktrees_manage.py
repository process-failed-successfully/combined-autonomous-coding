from main import run_worktrees
import unittest
from unittest.mock import patch
import subprocess
from pathlib import Path
import tempfile
import shutil
import argparse
import sys
import io

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestWorktreesManageAction(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()
        self.worktrees_dir = self.project_dir / "worktrees"
        self.worktrees_dir.mkdir()

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir)
        (self.project_dir / "initial_file.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)

        # Create a worktree
        self.worktree_name = "test-worktree"
        self.worktree_path = self.worktrees_dir / self.worktree_name
        subprocess.run(["git", "worktree", "add", str(self.worktree_path)], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.input', side_effect=['1', '1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_manage_action_show(self, mock_stdout, mock_input):
        args = argparse.Namespace(
            action="manage",
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Interactive Worktree Management ---", output)
        self.assertIn("[1] test-worktree (branch: test-worktree)", output)
        self.assertIn("Managing worktree: test-worktree", output)
        self.assertIn("[1] Show", output)
        self.assertIn("--- Executing 'SHOW' on 'test-worktree' ---", output)
        self.assertIn("✅ Worktree is clean.", output)

    @patch('builtins.input', side_effect=['1', '2', 'n'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_manage_action_diff(self, mock_stdout, mock_input):
        (self.worktree_path / "new_file.txt").write_text("new content")
        subprocess.run(["git", "add", "new_file.txt"], cwd=self.worktree_path, capture_output=True)

        args = argparse.Namespace(
            action="manage",
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Executing 'DIFF' on 'test-worktree' ---", output)
        self.assertIn("+++ b/new_file.txt", output)

    @patch('builtins.input', side_effect=['1', '3', 'y', 'n'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_manage_action_merge(self, mock_stdout, mock_input):
        (self.worktree_path / "merge_file.txt").write_text("merge content")
        subprocess.run(["git", "add", "merge_file.txt"], cwd=self.worktree_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Merge commit"], cwd=self.worktree_path, capture_output=True)

        args = argparse.Namespace(
            action="manage",
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Executing 'MERGE' on 'test-worktree' ---", output)
        self.assertIn("Merge successful.", output)

    @patch('builtins.input', side_effect=['1', '4', 'y'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_manage_action_revert(self, mock_stdout, mock_input):
        (self.worktree_path / "revert_file.txt").write_text("revert content")

        args = argparse.Namespace(
            action="manage",
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Executing 'REVERT' on 'test-worktree' ---", output)
        self.assertIn("✅ Revert complete. Worktree is now clean.", output)

    @patch('builtins.input', side_effect=['1', '5', 'n', 'y'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_manage_action_clean(self, mock_stdout, mock_input):
        args = argparse.Namespace(
            action="manage",
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Executing 'CLEAN' on 'test-worktree' ---", output)
        self.assertIn("✅ Removed worktree: test-worktree", output)


if __name__ == '__main__':
    unittest.main()
