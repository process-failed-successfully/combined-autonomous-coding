import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import argparse
import sys
import io

# It's challenging to import main.py directly due to its structure.
# A common pattern is to add the repo root to sys.path for testing.
sys.path.insert(0, str(Path(__file__).parent.parent))
import main

def mock_fs_check(path_obj):
    """A side effect for Path.exists and Path.is_dir to handle various test conditions."""
    # .git directory check
    if path_obj.name == '.git':
        return True
    # worktrees directory check for cleaning all
    if path_obj.name == 'worktrees':
        return True
    # Specific worktree directory check for show/clean
    if 'agent-sprint-task' in str(path_obj) or path_obj.name in ['wt1', 'wt2']:
        return True
    return False

class TestMainWorktrees(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path("/tmp/test_project")
        self.worktrees_dir = self.temp_dir / "worktrees"

    def _run_worktrees(self, args_list):
        """Helper to run the worktrees command with mocked args."""
        full_args = ['main.py', 'worktrees'] + args_list
        with patch('sys.argv', full_args), \
             patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                # We need to re-parse args inside the context manager
                # so it picks up the patched sys.argv
                args = main.parse_args()
                main.run_worktrees(args)
            except SystemExit as e:
                if e.code != 0:
                    raise
            return mock_stdout.getvalue()

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    def test_list_worktrees_success(self, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees list' with successful git output."""
        porcelain_output = (
            "worktree /tmp/test_project/worktrees/agent-sprint-task-1\n"
            "branch refs/heads/agent-sprint-task-1\n"
            "\n"
            "worktree /tmp/test_project/worktrees/agent-sprint-task-2\n"
            "HEAD 1234567890abcdef\n"
            "branch refs/heads/agent-sprint-task-2\n"
            "\n"
        )
        mock_run = MagicMock()
        mock_run.stdout = porcelain_output
        with patch('subprocess.run', return_value=mock_run) as mock_subprocess_run:
            output = self._run_worktrees(['list', '-p', str(self.temp_dir)])

            expected_cmd = ['/usr/bin/git', '-C', str(self.temp_dir), 'worktree', 'list', '--porcelain']
            mock_subprocess_run.assert_called_once_with(
                expected_cmd, capture_output=True, text=True, check=True
            )
            self.assertIn("agent-sprint-task-1 (branch: agent-sprint-task-1)", output)
            self.assertIn("agent-sprint-task-2 (branch: agent-sprint-task-2)", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    def test_list_worktrees_empty(self, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees list' when no agent worktrees are found."""
        porcelain_output = (
            "worktree /tmp/other_project/some-other-worktree\\n"
            "branch refs/heads/feature-branch\\n"
            "\\n"
        )
        mock_run = MagicMock()
        mock_run.stdout = porcelain_output
        with patch('subprocess.run', return_value=mock_run):
            output = self._run_worktrees(['list', '-p', str(self.temp_dir)])
            self.assertIn("No active agent worktrees found.", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    def test_show_worktree_clean(self, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees show' on a clean worktree."""
        mock_run = MagicMock()
        mock_run.stdout = ""
        with patch('subprocess.run', return_value=mock_run) as mock_subprocess_run:
            output = self._run_worktrees(['show', 'agent-sprint-task-1', '-p', str(self.temp_dir)])

            expected_cmd = ['/usr/bin/git', '-C', str(self.worktrees_dir / 'agent-sprint-task-1'), 'status', '--porcelain']
            mock_subprocess_run.assert_called_once_with(
                expected_cmd, capture_output=True, text=True, check=True
            )
            self.assertIn("✅ Worktree is clean.", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    def test_show_worktree_dirty(self, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees show' on a worktree with uncommitted changes."""
        mock_run = MagicMock()
        mock_run.stdout = " M README.md\\n?? new_file.txt"
        with patch('subprocess.run', return_value=mock_run):
            output = self._run_worktrees(['show', 'agent-sprint-task-1', '-p', str(self.temp_dir)])
            self.assertIn("Uncommitted changes:", output)
            self.assertIn("M README.md", output)
            self.assertIn("?? new_file.txt", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    @patch('builtins.input', return_value='y')
    def test_clean_single_worktree_yes(self, mock_input, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees clean <name>' with user confirmation."""
        with patch('subprocess.run') as mock_subprocess_run:
            output = self._run_worktrees(['clean', 'agent-sprint-task-1', '-p', str(self.temp_dir)])

            expected_cmd = ['/usr/bin/git', '-C', str(self.temp_dir), 'worktree', 'remove', 'agent-sprint-task-1']
            mock_subprocess_run.assert_called_once_with(
                expected_cmd, check=True, capture_output=True, text=True
            )
            self.assertIn("Removed worktree: agent-sprint-task-1", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    @patch('builtins.input', return_value='n')
    def test_clean_single_worktree_no(self, mock_input, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees clean <name>' with user aborting."""
        with patch('subprocess.run') as mock_subprocess_run:
            output = self._run_worktrees(['clean', 'agent-sprint-task-1', '-p', str(self.temp_dir)])

            mock_subprocess_run.assert_not_called()
            self.assertIn("Aborted.", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    def test_clean_single_worktree_force(self, mock_exists, mock_is_dir, mock_which):
        """Test 'worktrees clean <name> --force --yes'."""
        with patch('subprocess.run') as mock_subprocess_run:
            output = self._run_worktrees(['clean', 'agent-sprint-task-1', '--force', '--yes', '-p', str(self.temp_dir)])

            expected_cmd = ['/usr/bin/git', '-C', str(self.temp_dir), 'worktree', 'remove', '--force', 'agent-sprint-task-1']
            mock_subprocess_run.assert_called_once_with(
                expected_cmd, check=True, capture_output=True, text=True
            )
            self.assertIn("Removed worktree: agent-sprint-task-1", output)

    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('pathlib.Path.iterdir', return_value=[Path('/tmp/test_project/worktrees/wt1'), Path('/tmp/test_project/worktrees/wt2')])
    @patch('pathlib.Path.is_dir', side_effect=mock_fs_check, autospec=True)
    @patch('pathlib.Path.exists', side_effect=mock_fs_check, autospec=True)
    def test_clean_all_worktrees_yes(self, mock_exists, mock_is_dir, mock_iterdir, mock_which):
        """Test 'worktrees clean --yes' to remove all worktrees."""
        with patch('subprocess.run') as mock_subprocess_run:
            output = self._run_worktrees(['clean', '--yes', '-p', str(self.temp_dir)])

            calls = [
                call(['/usr/bin/git', '-C', str(self.temp_dir), 'worktree', 'remove', 'wt1'], check=True, capture_output=True, text=True),
                call(['/usr/bin/git', '-C', str(self.temp_dir), 'worktree', 'remove', 'wt2'], check=True, capture_output=True, text=True)
            ]
            mock_subprocess_run.assert_has_calls(calls, any_order=True)
            self.assertIn("Removed worktree: wt1", output)
            self.assertIn("Removed worktree: wt2", output)

if __name__ == '__main__':
    unittest.main()
