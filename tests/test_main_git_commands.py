import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import sys
import argparse
import io
from contextlib import redirect_stderr

# Add the parent directory to the sys.path to allow imports from the 'shared' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_git_command
from shared.cli_utils import _run_blame_logic

class TestGitCommands(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a git repository."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        self.git_path = shutil.which("git")
        if not self.git_path:
            self.skipTest("git executable not found")

        # Initialize a git repository
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)

        # Create an initial commit
        (self.project_dir / "README.md").write_text("Initial commit")
        subprocess.run([self.git_path, "add", "README.md"], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)
        self.initial_commit_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True
        ).strip()


    def tearDown(self):
        """Remove the temporary directory and restore CWD."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def _get_current_branch(self):
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def _commit_file(self, filename, content, message):
        """Helper to write a file and commit it."""
        (self.project_dir / filename).write_text(content)
        subprocess.run([self.git_path, "add", filename], cwd=self.project_dir, check=True)
        subprocess.run([self.git_path, "commit", "-m", message], cwd=self.project_dir, check=True)
        # Get the commit hash
        result = subprocess.run([self.git_path, "rev-parse", "HEAD"], cwd=self.project_dir, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    # --- Tests from test_main_commit.py ---

    @patch('subprocess.run')
    @patch('builtins.input')
    @patch('shutil.which', return_value='/usr/bin/git')
    def test_git_commit_interactive(self, mock_which, mock_input, mock_subprocess_run):
        mock_input.side_effect = ['feat', 'cli', 'Add new commit command', '', 'n', 'y']

        def side_effect(*args, **kwargs):
            command = args[0]
            if 'diff' in command:
                return MagicMock(returncode=1) # Simulate changes
            return MagicMock(returncode=0, stdout="Success")
        mock_subprocess_run.side_effect = side_effect

        args = argparse.Namespace(
            git_command="commit",
            message=None,
            run_tests=False,
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        expected_message = "feat(cli): Add new commit command"

        commit_call = call([mock_which.return_value, '-C', str(self.project_dir), 'commit', '-m', expected_message], check=True, capture_output=True, text=True)
        mock_subprocess_run.assert_has_calls([
            call([mock_which.return_value, '-C', str(self.project_dir), 'add', '-A'], check=True, capture_output=True, text=True),
            call([mock_which.return_value, '-C', str(self.project_dir), 'diff', '--cached', '--quiet'], capture_output=True),
            commit_call
        ], any_order=True)

    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    def test_git_commit_non_interactive(self, mock_which, mock_subprocess_run):
        commit_message = "feat: a regular commit"

        def side_effect(*args, **kwargs):
            command = args[0]
            if 'diff' in command:
                return MagicMock(returncode=1) # Simulate changes
            return MagicMock(returncode=0, stdout="Success")
        mock_subprocess_run.side_effect = side_effect

        args = argparse.Namespace(
            git_command="commit",
            message=commit_message,
            run_tests=False,
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        commit_call = call([mock_which.return_value, '-C', str(self.project_dir), 'commit', '-m', commit_message], check=True, capture_output=True, text=True)
        mock_subprocess_run.assert_has_calls([commit_call])

    # --- Tests from test_main_push.py ---

    @patch('shared.git.get_current_branch', return_value='feature-branch')
    @patch('subprocess.run')
    def test_git_push_success(self, mock_run, mock_get_branch):
        mock_run.side_effect = [
            MagicMock(stdout="", returncode=0),  # Clean status
            MagicMock(returncode=0)              # Successful push
        ]
        args = argparse.Namespace(git_command="push", project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        expected_push_cmd = [self.git_path, "-C", str(self.project_dir), "push", "-u", "origin", "feature-branch"]
        self.assertEqual(mock_run.call_count, 2)
        actual_cmd = mock_run.call_args_list[1].args[0]
        self.assertEqual(actual_cmd, expected_push_cmd)

    def test_git_push_to_protected_branch_denied(self):
        for branch in ['main', 'master']:
            with self.subTest(branch=branch):
                if branch == 'main':
                    subprocess.run([self.git_path, "checkout", "main"], cwd=self.project_dir, check=True, capture_output=True)
                else:
                    subprocess.run([self.git_path, "checkout", "-b", branch], cwd=self.project_dir, check=True, capture_output=True)

                args = argparse.Namespace(git_command="push", project_dir=self.project_dir)
                with self.assertRaises(SystemExit) as cm:
                    run_git_command(args)
                self.assertEqual(cm.exception.code, 1)

    # --- Tests from test_main_pull.py ---

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_git_pull_success(self, mock_which, mock_run):
        mock_which.return_value = self.git_path
        mock_run.side_effect = [
            MagicMock(stdout=b'', returncode=0),  # Clean status
            MagicMock(returncode=0)               # Successful pull
        ]
        args = argparse.Namespace(git_command="pull", project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_run.call_count, 2)
        expected_pull_cmd = [self.git_path, "-C", str(self.project_dir), "pull"]
        mock_run.assert_called_with(expected_pull_cmd, text=True)

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_git_pull_with_uncommitted_changes(self, mock_which, mock_run):
        mock_which.return_value = self.git_path
        mock_run.return_value = MagicMock(stdout=b' M README.md', returncode=0) # Simulate uncommitted changes

        args = argparse.Namespace(git_command="pull", project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run.assert_called_once()

    # --- Tests from test_main_log.py ---

    @patch('main.subprocess.run')
    def test_git_log_success(self, mock_subprocess_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process
        args = argparse.Namespace(git_command="log", project_dir=self.project_dir, count=None)

        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)
        self.assertEqual(cm.exception.code, 0)

        mock_subprocess_run.assert_called_once()
        called_command = mock_subprocess_run.call_args[0][0]
        self.assertIn("log", called_command)

    @patch('main.subprocess.run')
    def test_git_log_with_count(self, mock_subprocess_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process
        args = argparse.Namespace(git_command="log", project_dir=self.project_dir, count=2)

        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)
        self.assertEqual(cm.exception.code, 0)

        mock_subprocess_run.assert_called_once()
        called_command = mock_subprocess_run.call_args[0][0]
        self.assertIn("-n", called_command)
        self.assertIn("2", called_command)

    # --- Tests from test_main_diff.py ---

    @patch('main.subprocess.run')
    def test_git_diff_uncommitted_changes(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        args = argparse.Namespace(git_command="diff", target=None, project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_once()
        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn("diff", called_args)
        self.assertIn("HEAD", called_args)

    # --- Tests from test_main_blame.py ---
    def test_git_blame_with_run_id(self):
        """Test blaming a file where a commit has a Run ID."""
        self._commit_file("test.txt", "line 1\n", "Initial commit")
        agent_commit_msg = "Agent modification\n\nRun ID: 20240101-120000-test-agent"
        self._commit_file("test.txt", "line 1\nline 2\n", agent_commit_msg)

        args = argparse.Namespace(
            git_command="blame",
            project_dir=self.project_dir,
            filepath=self.project_dir / "test.txt"
        )

        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)
        self.assertEqual(cm.exception.code, 0)

    # --- Tests from test_main_discard.py ---

    def test_git_discard_all_changes(self):
        """Test discarding all changes with --yes."""
        (self.project_dir / "modified_file.txt").write_text("modified content")
        (self.project_dir / "untracked_file.txt").write_text("untracked content")

        args = argparse.Namespace(git_command="discard", files=[], interactive=False, yes=True, project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse((self.project_dir / "untracked_file.txt").exists())

    # --- Tests from test_main_undo.py ---

    @patch('builtins.input', return_value='1')
    def test_git_undo_restores_stashed_changes(self, mock_input):
        (self.project_dir / "new_file.txt").write_text("new file content")

        discard_args = argparse.Namespace(git_command="discard", files=[], interactive=False, yes=True, project_dir=self.project_dir)
        with self.assertRaises(SystemExit):
            run_git_command(discard_args)

        undo_args = argparse.Namespace(git_command="undo", project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            run_git_command(undo_args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.project_dir / "new_file.txt").exists())

    # --- Tests from test_main_rewind.py ---

    def test_git_rewind_to_specific_commit(self):
        args = argparse.Namespace(git_command="rewind", target=self.initial_commit_hash, project_dir=self.project_dir, yes=True)
        with self.assertRaises(SystemExit) as cm:
            run_git_command(args)

        self.assertEqual(cm.exception.code, 0)
        current_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=self.project_dir, text=True).strip()
        self.assertEqual(current_hash, self.initial_commit_hash)

    # --- Tests from test_main_branch.py ---

    @patch('main.sys.exit')
    def test_git_branch_create(self, mock_exit):
        args = MagicMock()
        args.git_command = "branch"
        args.project_dir = self.project_dir
        args.action = "create"
        args.branch_name = "feature-branch"
        run_git_command(args)
        self.assertEqual(self._get_current_branch(), "feature-branch")

if __name__ == '__main__':
    unittest.main()
