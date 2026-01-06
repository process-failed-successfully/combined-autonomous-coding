import unittest
from unittest.mock import patch, MagicMock, call
import argparse
from pathlib import Path
import json
import sys
import io

# Make sure the main script can be imported
from main import run_sprint_command, parse_args

class TestSprintCommand(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for our tests
        self.test_dir = Path("test_sprint_project")
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / ".git").mkdir(exist_ok=True)
        self.worktrees_dir = self.test_dir / "worktrees"
        self.worktrees_dir.mkdir(exist_ok=True)

        # Create mock sprint_plan.json
        self.sprint_plan = {
            "sprint_goal": "Implement user authentication",
            "tasks": [
                {"id": "task-1", "title": "Create login endpoint", "description": "..."},
                {"id": "task-2", "title": "Create user model", "description": "..."},
                {"id": "task-3", "title": "Implement JWT", "description": "..."}
            ]
        }
        (self.test_dir / "sprint_plan.json").write_text(json.dumps(self.sprint_plan))

        # Create mock feature_list.json
        self.feature_list = [
            {"name": "User Login", "status": "completed"},
            {"name": "User Registration", "status": "in_progress"}
        ]
        (self.test_dir / "feature_list.json").write_text(json.dumps(self.feature_list))

    def tearDown(self):
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('main.shutil.which')
    @patch('main.subprocess.run')
    def test_sprint_status_success(self, mock_subprocess_run, mock_shutil_which):
        """Test the 'sprint status' command with a valid setup."""
        mock_shutil_which.return_value = "/usr/bin/git"

        def mock_git_calls(*args, **kwargs):
            cmd = args[0]
            if "worktree" in cmd and "list" in cmd:
                mock_porcelain_output = (
                    f"worktree {(self.worktrees_dir / 'task-1').resolve()}\n"
                    "branch refs/heads/sprint/task-1\n\n"
                    f"worktree {(self.worktrees_dir / 'task-2').resolve()}\n"
                    "branch refs/heads/sprint/task-2\n\n"
                )
                return MagicMock(stdout=mock_porcelain_output, returncode=0)
            elif "status" in cmd:
                if "task-1" in str(cmd[2]):
                    return MagicMock(stdout=" M main.py\n", returncode=0)
                elif "task-2" in str(cmd[2]):
                    return MagicMock(stdout="", returncode=0)
            elif "show-ref" in cmd:
                # This will be called for task-3, which has no worktree
                raise subprocess.CalledProcessError(1, cmd)
            return MagicMock(stdout="", returncode=0)

        mock_subprocess_run.side_effect = mock_git_calls
        args = parse_args(["sprint", "status", "-p", str(self.test_dir)])

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_sprint_command(args)
            self.assertEqual(cm.exception.code, 0)

        output = mock_stdout.getvalue()

        # Assertions
        self.assertIn("--- Sprint Status", output)
        self.assertIn("[ Overall Progress: 1/2 features completed ]", output)
        self.assertIn("[ Current Sprint Goal: Implement user authentication ]", output)
        self.assertIn("Create login endpoint", output)
        self.assertIn("In Progress (Changes) on branch 'sprint/task-1'", output)
        self.assertIn("Create user model", output)
        self.assertIn("In Progress (Clean) on branch 'sprint/task-2'", output)
        self.assertIn("Implement JWT", output)
        self.assertIn("Pending / Completed", output)
        self.assertIn("sprint diff task-1", output)

    @patch('main.run_worktrees')
    def test_sprint_diff_shortcut(self, mock_run_worktrees):
        """Test the 'sprint diff' shortcut command."""
        args = parse_args(["sprint", "diff", "task-123", "-p", str(self.test_dir)])
        run_sprint_command(args)

        # Check that run_worktrees was called with the correct translated arguments
        mock_run_worktrees.assert_called_once()
        call_args = mock_run_worktrees.call_args[0][0]
        self.assertEqual(call_args.action, "diff")
        self.assertEqual(call_args.worktree_name, "task-123")
        self.assertEqual(call_args.project_dir, self.test_dir)

    @patch('main.run_worktrees')
    def test_sprint_merge_shortcut(self, mock_run_worktrees):
        """Test the 'sprint merge' shortcut command."""
        args = parse_args(["sprint", "merge", "task-abc", "--clean", "-y", "-p", str(self.test_dir)])
        run_sprint_command(args)

        mock_run_worktrees.assert_called_once()
        call_args = mock_run_worktrees.call_args[0][0]
        self.assertEqual(call_args.action, "merge")
        self.assertEqual(call_args.worktree_name, "task-abc")
        self.assertEqual(call_args.project_dir, self.test_dir)
        self.assertTrue(call_args.clean)
        self.assertTrue(call_args.yes)

if __name__ == '__main__':
    unittest.main()
