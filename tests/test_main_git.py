import unittest
from unittest.mock import patch, MagicMock
import subprocess
import tempfile
import shutil
from pathlib import Path
import sys
import argparse
import io
import contextlib

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_git, get_parser, parse_args

class TestGitProxyCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a git environment with a worktree."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.test_dir.name)

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        (self.project_dir / "README.md").write_text("Initial commit")
        subprocess.run(["git", "add", "README.md"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True, capture_output=True)

        # Create a real worktree
        self.task_id = "test-task-001"
        self.worktree_name = f"sprint-task-{self.task_id}"
        self.worktree_relative_path = Path("worktrees") / self.worktree_name
        self.worktree_path = self.project_dir / self.worktree_relative_path
        subprocess.run(
            ["git", "worktree", "add", str(self.worktree_relative_path)],
            cwd=self.project_dir,
            check=True,
            capture_output=True
        )

    def tearDown(self):
        """Clean up the temporary directory and git worktree."""
        try:
            subprocess.run(["git", "worktree", "remove", str(self.worktree_relative_path)], cwd=self.project_dir, capture_output=True)
        except Exception:
            pass
        self.test_dir.cleanup()

    @patch("subprocess.run")
    def test_run_git_proxy_success(self, mock_subprocess_run):
        """Test that the git proxy command successfully calls subprocess.run."""
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        git_command_args = ["status", "--porcelain"]
        args = argparse.Namespace(
            project_dir=self.project_dir,
            task=self.task_id,
            git_args=git_command_args
        )

        with self.assertRaises(SystemExit) as cm:
            run_git(args)

        self.assertEqual(cm.exception.code, 0)
        expected_command = [shutil.which("git")] + git_command_args
        mock_subprocess_run.assert_called_once_with(
            expected_command,
            cwd=self.worktree_path,
            capture_output=True,
            text=True
        )

    def test_run_git_proxy_missing_task(self):
        """Test that the command exits with an error if the --task argument is missing."""
        args = argparse.Namespace(project_dir=self.project_dir, task=None, git_args=["status"])
        stderr_catcher = io.StringIO()
        with contextlib.redirect_stderr(stderr_catcher):
            with self.assertRaises(SystemExit) as cm:
                run_git(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("The '--task' argument is required", stderr_catcher.getvalue())

    def test_run_git_proxy_no_command(self):
        """Test that the command exits with an error if no git command is provided."""
        args = argparse.Namespace(project_dir=self.project_dir, task=self.task_id, git_args=[])
        stderr_catcher = io.StringIO()
        with contextlib.redirect_stderr(stderr_catcher):
            with self.assertRaises(SystemExit) as cm:
                run_git(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("No git command provided", stderr_catcher.getvalue())

    def test_run_git_proxy_worktree_not_found(self):
        """Test that the command exits with an error if the worktree directory does not exist."""
        invalid_task_id = "non-existent-task"
        args = argparse.Namespace(project_dir=self.project_dir, task=invalid_task_id, git_args=["status"])
        stderr_catcher = io.StringIO()
        with contextlib.redirect_stderr(stderr_catcher):
            with self.assertRaises(SystemExit) as cm:
                run_git(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(f"Worktree for task '{invalid_task_id}' not found", stderr_catcher.getvalue())

    def test_parse_args_git_command(self):
        """Test that argparse correctly parses the 'git' subcommand and its arguments."""
        argv = [
            "git", "--task", self.task_id, "--project-dir", str(self.project_dir),
            "log", "-n", "1", "--oneline"
        ]
        parser = get_parser()
        args = parse_args(parser, argv)

        self.assertEqual(args.command, "git")
        self.assertEqual(args.task, self.task_id)
        self.assertEqual(args.project_dir, self.project_dir)
        self.assertEqual(args.git_args, ["log", "-n", "1", "--oneline"])

    def test_integration_git_status_in_worktree(self):
        """Perform an integration test by running a real git status command."""
        (self.worktree_path / "new_file.txt").write_text("Hello from the worktree")

        argv = ["git", "--task", self.task_id, "--project-dir", str(self.project_dir), "status", "--porcelain"]
        parser = get_parser()
        args = parse_args(parser, argv)

        stdout_catcher = io.StringIO()
        with contextlib.redirect_stdout(stdout_catcher):
            with self.assertRaises(SystemExit) as cm:
                run_git(args)

        self.assertEqual(cm.exception.code, 0)
        output = stdout_catcher.getvalue().strip()
        self.assertEqual(output, "?? new_file.txt")

if __name__ == "__main__":
    unittest.main()
