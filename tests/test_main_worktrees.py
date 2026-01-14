import unittest
from unittest.mock import patch, call
import subprocess
import tempfile
import shutil
from pathlib import Path
import io
from contextlib import redirect_stdout, redirect_stderr

from main import get_parser, parse_args

class TestWorktreesCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir) / "project"
        self.project_dir.mkdir()

        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        (self.project_dir / "README.md").write_text("initial commit")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_worktree_create(self):
        parser = get_parser()
        args = parse_args(parser, ["worktrees", "create", "test-worktree", "-p", str(self.project_dir)])
        with patch("sys.exit") as mock_exit:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)

        worktree_path = self.project_dir / "worktrees" / "test-worktree"
        self.assertTrue(worktree_path.is_dir())

        result = subprocess.run(["git", "worktree", "list"], cwd=self.project_dir, capture_output=True, text=True)
        self.assertIn(str(worktree_path), result.stdout)

    def test_worktree_list(self):
        subprocess.run(["git", "worktree", "add", "worktrees/test-worktree-1"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "worktree", "add", "worktrees/test-worktree-2"], cwd=self.project_dir, capture_output=True)

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "list", "-p", str(self.project_dir)])
        with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)

            self.assertIn(call("  - test-worktree-1 (branch: test-worktree-1)"), mock_print.call_args_list)
            self.assertIn(call("  - test-worktree-2 (branch: test-worktree-2)"), mock_print.call_args_list)

    def test_worktree_show_sprint_worktree(self):
        # Setup: Create a real worktree and a sprint plan
        worktree_name = "sprint-task-123"
        worktree_path = self.project_dir / "worktrees" / worktree_name
        subprocess.run(["git", "worktree", "add", str(worktree_path)], cwd=self.project_dir, capture_output=True)

        sprint_plan = {
            "tasks": [
                {
                    "id": "123",
                    "title": "Implement feature X",
                    "description": "This is a test task."
                }
            ]
        }
        (self.project_dir / "sprint_plan.json").write_text(str(sprint_plan).replace("'", '"'))

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "show", worktree_name, "-p", str(self.project_dir)])

        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                from main import run_worktrees
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = f.getvalue()

        self.assertIn(f"Dashboard for Worktree: {worktree_name}", output)
        self.assertIn("Sprint Task Info", output)
        self.assertIn("Implement feature X", output)
        self.assertIn("This is a test task.", output)
        self.assertIn("Worktree is clean", output)

    def test_worktree_show_clean_worktree(self):
        # Setup: Create a real worktree
        worktree_name = "clean-worktree"
        worktree_path = self.project_dir / "worktrees" / worktree_name
        subprocess.run(["git", "worktree", "add", str(worktree_path)], cwd=self.project_dir, capture_output=True)

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "show", worktree_name, "-p", str(self.project_dir)])

        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                from main import run_worktrees
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 0)
        output = f.getvalue()

        self.assertIn(f"Dashboard for Worktree: {worktree_name}", output)
        self.assertIn("Worktree is clean", output)
        self.assertIn("No differences with HEAD", output)

    def test_worktree_show_non_existent_worktree(self):
        parser = get_parser()
        args = parse_args(parser, ["worktrees", "show", "non-existent-worktree", "-p", str(self.project_dir)])

        f = io.StringIO()
        with redirect_stderr(f):
            with self.assertRaises(SystemExit) as cm:
                from main import run_worktrees
                run_worktrees(args)

        self.assertEqual(cm.exception.code, 1)
        output = f.getvalue()
        self.assertIn("Worktree 'non-existent-worktree' not found", output)

    def test_worktree_clean(self):
        worktree_path = self.project_dir / "worktrees" / "test-worktree"
        subprocess.run(["git", "worktree", "add", str(worktree_path)], cwd=self.project_dir, capture_output=True)
        self.assertTrue(worktree_path.exists())

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "clean", "test-worktree", "-p", str(self.project_dir), "-y"])
        with patch("sys.exit") as mock_exit:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)

        self.assertFalse(worktree_path.exists())

    def test_worktree_revert(self):
        worktree_path = self.project_dir / "worktrees" / "test-worktree"
        subprocess.run(["git", "worktree", "add", str(worktree_path)], cwd=self.project_dir, capture_output=True)
        (worktree_path / "new_file.txt").write_text("uncommitted change")

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "revert", "test-worktree", "-p", str(self.project_dir), "-y"])
        with patch("sys.exit") as mock_exit:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)

        result = subprocess.run(["git", "status", "--porcelain"], cwd=worktree_path, capture_output=True, text=True)
        self.assertEqual(result.stdout.strip(), "")

    def test_worktree_merge(self):
        worktree_path = self.project_dir / "worktrees" / "test-worktree"
        subprocess.run(["git", "worktree", "add", "-b", "feature-branch", str(worktree_path)], cwd=self.project_dir, capture_output=True)
        (worktree_path / "feature.txt").write_text("new feature")
        subprocess.run(["git", "add", "."], cwd=worktree_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add feature"], cwd=worktree_path, capture_output=True)

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "merge", "test-worktree", "-p", str(self.project_dir), "--clean", "-y"])
        with patch("sys.exit") as mock_exit:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)

        result = subprocess.run(["git", "log", "--oneline"], cwd=self.project_dir, capture_output=True, text=True)
        self.assertIn("Merge branch 'feature-branch'", result.stdout)
        self.assertFalse(worktree_path.exists())

    def test_worktree_diff(self):
        worktree_path = self.project_dir / "worktrees" / "test-worktree"
        subprocess.run(["git", "worktree", "add", str(worktree_path)], cwd=self.project_dir, capture_output=True)
        (worktree_path / "new_file.txt").write_text("diff content")
        subprocess.run(["git", "add", "new_file.txt"], cwd=worktree_path, capture_output=True)

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "diff", "test-worktree", "-p", str(self.project_dir)])
        with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)

            output = "".join([str(call_arg) for call_arg in mock_print.call_args_list])
            self.assertIn("diff --git", output)
            self.assertIn("new_file.txt", output)
            self.assertIn("+diff content", output)

    @patch("builtins.input", side_effect=["1", "1", "exit"])
    def test_worktree_manage_show(self, mock_input):
        worktree_path = self.project_dir / "worktrees" / "test-worktree"
        subprocess.run(["git", "worktree", "add", str(worktree_path)], cwd=self.project_dir, capture_output=True)
        (worktree_path / "new_file.txt").write_text("uncommitted change")

        parser = get_parser()
        args = parse_args(parser, ["worktrees", "manage", "-p", str(self.project_dir)])
        with patch("sys.exit") as mock_exit, patch("builtins.print") as mock_print:
            from main import run_worktrees
            run_worktrees(args)
            mock_exit.assert_called_once_with(0)
            mock_print.assert_any_call("  ?? new_file.txt")

if __name__ == "__main__":
    unittest.main()
