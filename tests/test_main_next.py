import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import subprocess
import sys
import argparse

# Make sure the main module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_next
from shared.cli_utils import get_suggestions, run_next_logic

class TestNextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository for testing
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir)
        (self.project_dir / "test.txt").write_text("initial commit")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shared.cli_utils.get_suggestions')
    @patch('main.run_next_logic')
    def test_run_next_invokes_logic(self, mock_run_next_logic, mock_get_suggestions):
        """Test that the top-level `run_next` command correctly calls the underlying logic function."""
        args = argparse.Namespace(project_dir=self.project_dir, yes=False)

        with self.assertRaises(SystemExit) as cm:
            run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_next_logic.assert_called_once()
        # Check that the arguments are passed correctly
        call_args = mock_run_next_logic.call_args[1]
        self.assertEqual(call_args['project_dir'], self.project_dir)
        self.assertEqual(call_args['yes'], False)
        self.assertTrue('executable_name' in call_args)

    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_suggests_commit_with_uncommitted_changes(self, mock_subprocess_run, mock_input):
        """Test that 'commit' is suggested and executed when there are uncommitted changes."""
        # Let the real git status run, but mock the final execution
        (self.project_dir / "new_file.txt").write_text("some changes")

        executable_name = "main.py"

        # We only want to mock the final call that executes the command
        with patch('shared.cli_utils.subprocess.run') as mock_final_run:
            run_next_logic(project_dir=self.project_dir, yes=False, executable_name=executable_name)
            mock_final_run.assert_called_once()
            executed_command_args = mock_final_run.call_args.args[0]
            self.assertIn("commit", executed_command_args)

    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_suggests_test_after_commit(self, mock_subprocess_run, mock_input):
        """Test that 'test' is suggested when the repo is clean and in progress."""
        # Mock git status to return clean
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="", returncode=0), # git status -> clean
            MagicMock(stdout="main", returncode=0), # git branch
            MagicMock(returncode=0) # run test command
        ]

        executable_name = "main.py"
        run_next_logic(project_dir=self.project_dir, yes=False, executable_name=executable_name)

        executed_command_args = mock_subprocess_run.call_args.args[0]
        self.assertIn("test", executed_command_args)

    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_suggests_pr_create_when_qa_passed(self, mock_subprocess_run, mock_input):
        """Test that 'pr create' is suggested at the QA_PASSED stage."""
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "QA_PASSED").touch()

        # Create and checkout a feature branch
        subprocess.run(["git", "checkout", "-b", "feature/test-branch"], cwd=self.project_dir, capture_output=True)

        # Mock git status, branch, and push status
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="", returncode=0), # git status -> clean
            MagicMock(stdout="feature/test-branch", returncode=0), # get branch
            MagicMock(returncode=0), # ls-remote (branch is pushed)
            MagicMock(returncode=0) # run pr create command
        ]

        executable_name = "main.py"
        run_next_logic(project_dir=self.project_dir, yes=False, executable_name=executable_name)

        executed_command_args = mock_subprocess_run.call_args.args[0]
        self.assertIn("pr", executed_command_args)
        self.assertIn("create", executed_command_args)

    @patch('builtins.input', return_value='y')
    @patch('subprocess.run')
    def test_suggests_push_for_unpushed_branch(self, mock_subprocess_run, mock_input):
        """Test that 'push' is suggested for a feature branch with unpushed commits."""
        subprocess.run(["git", "checkout", "-b", "feature/unpushed"], cwd=self.project_dir, capture_output=True)
        (self.project_dir / "another.txt").write_text("work")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feat: add work"], cwd=self.project_dir, capture_output=True)

        # Mock git status (clean), get branch, and ls-remote (unpushed)
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="", returncode=0), # git status -> clean
            MagicMock(stdout="feature/unpushed", returncode=0), # get branch
            MagicMock(returncode=1), # ls-remote -> branch not found on remote
            MagicMock(returncode=0) # run push command
        ]

        executable_name = "main.py"
        run_next_logic(project_dir=self.project_dir, yes=False, executable_name=executable_name)

        executed_command_args = mock_subprocess_run.call_args.args[0]
        self.assertIn("push", executed_command_args)

    @patch('shared.cli_utils.subprocess.run')
    def test_yes_flag_skips_prompt(self, mock_subprocess_run):
        """Test that the -y flag executes the command without user input."""
        (self.project_dir / "new_file.txt").write_text("some changes")

        executable_name = "main.py"
        run_next_logic(project_dir=self.project_dir, yes=True, executable_name=executable_name)

        # Check that the 'commit' command was executed directly
        mock_subprocess_run.assert_called_once()
        executed_command_args = mock_subprocess_run.call_args.args[0]
        self.assertIn("commit", executed_command_args)

    @patch('builtins.input', return_value='n')
    @patch('shared.cli_utils.subprocess.run')
    def test_user_can_decline_execution(self, mock_subprocess_run, mock_input):
        """Test that the command is not executed if the user declines."""
        (self.project_dir / "new_file.txt").write_text("some changes")

        with self.assertRaises(SystemExit) as cm:
            executable_name = "main.py"
            run_next_logic(project_dir=self.project_dir, yes=False, executable_name=executable_name)

        self.assertEqual(cm.exception.code, 0)
        # Verify that no command was executed
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
