import unittest
from unittest.mock import patch, MagicMock, call, AsyncMock
import argparse
from pathlib import Path
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_commit

class TestCommitCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and initialize a git repository."""
        self.test_dir = Path("test_project_commit")
        self.test_dir.mkdir(exist_ok=True)
        self.original_cwd = Path.cwd()
        os.chdir(self.test_dir)

        import subprocess
        # Initialize a git repository
        self.git_path = "git"
        subprocess.run([self.git_path, "init", "-b", "main"], check=True, capture_output=True)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], check=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], check=True)
        (Path.cwd() / "initial_file.txt").write_text("initial content")
        subprocess.run([self.git_path, "add", "."], check=True)
        subprocess.run([self.git_path, "commit", "-m", "Initial commit"], check=True, capture_output=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    def test_commit_basic(self, mock_run, mock_which):
        """Test basic commit functionality."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message="Test commit",
            run_tests=False,
            generate=False
        )

        # Mock the git commands. `git diff --cached --quiet` returns 1 if there are changes.
        mock_diff_with_changes = MagicMock(returncode=1)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # git add -A
            mock_diff_with_changes, # git diff --cached --quiet
            MagicMock(returncode=0, stdout="[main 1234567] Test commit", stderr="") # git commit
        ]

        (Path.cwd() / "new_file.txt").write_text("new content")

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)
        self.assertEqual(cm.exception.code, 0)

        # Since we're in a temporary directory, we can't hardcode the path
        # Let's check the calls more flexibly
        self.assertEqual(mock_run.call_count, 3)
        self.assertEqual(mock_run.call_args_list[0].args[0][3], 'add')
        self.assertEqual(mock_run.call_args_list[1].args[0][3], 'diff')
        self.assertEqual(mock_run.call_args_list[2].args[0][3], 'commit')


    @patch('main.shutil.which', return_value='git')
    @patch('main.run_test')
    @patch('main.subprocess.run')
    def test_commit_with_tests_success(self, mock_subprocess_run, mock_run_test, mock_which):
        """Test commit with successful tests."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message="Test commit with tests",
            run_tests=True,
            generate=False
        )
        mock_run_test.return_value = None # Simulate successful test run

        # Mocks for git commands
        mock_diff_with_changes = MagicMock(returncode=1)
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            mock_diff_with_changes, # git diff
            MagicMock(returncode=0, stdout="[main 2345678] Test commit with tests", stderr="") # git commit
        ]

        (Path.cwd() / "new_file.txt").write_text("some content")

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_test.assert_called_once()
        self.assertTrue(mock_subprocess_run.call_count >= 2)


    @patch('main.shutil.which', return_value='git')
    @patch('main.run_test')
    @patch('main.subprocess.run')
    def test_commit_with_tests_failure(self, mock_subprocess_run, mock_run_test, mock_which):
        """Test that commit is aborted when tests fail."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message="This should not be committed",
            run_tests=True,
            generate=False
        )
        # Simulate a test failure by raising SystemExit with a non-zero code
        mock_run_test.side_effect = SystemExit(1)

        (Path.cwd() / "new_file.txt").write_text("some content")

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run_test.assert_called_once()

        # Ensure git commit was NOT called
        for call_args in mock_subprocess_run.call_args_list:
            self.assertNotIn('commit', call_args[0][0])

    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    def test_commit_no_changes(self, mock_run, mock_which):
        """Test that commit does nothing if there are no changes."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message="No changes",
            run_tests=False,
            generate=False
        )

        # Mock git diff to return 0 (no changes)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""), # git add
            MagicMock(returncode=0), # git diff
        ]


        with self.assertRaises(SystemExit) as cm:
            run_commit(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify that `git commit` was not called
        for call_args in mock_run.call_args_list:
            self.assertNotIn('commit', call_args[0][0])


    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    def test_commit_deletion(self, mock_run, mock_which):
        """Test that deleting a file is correctly staged and committed."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message="Delete file",
            run_tests=False,
            generate=False
        )

        # Mock the git commands
        mock_diff_with_changes = MagicMock(returncode=1)
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # git add -A
            mock_diff_with_changes, # git diff --cached --quiet (returns 1 for changes)
            MagicMock(returncode=0, stdout="[main 3456789] Delete file", stderr="") # git commit
        ]

        # Delete the initial file
        (Path.cwd() / "initial_file.txt").unlink()

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)
        self.assertEqual(cm.exception.code, 0)

        # Check that 'git add -A' was called
        add_call = mock_run.call_args_list[0].args[0]
        self.assertIn('add', add_call)
        self.assertIn('-A', add_call)

        # Check that `git commit` was called
        commit_call = mock_run.call_args_list[2].args[0]
        self.assertIn('commit', commit_call)


    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    @patch('main.GeminiAgent')
    @patch('builtins.input', side_effect=['y'])
    def test_commit_with_generate_happy_path(self, mock_input, mock_gemini_agent, mock_run, mock_which):
        """Test AI commit message generation happy path."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message=None,
            run_tests=False,
            generate=True
        )

        mock_agent_instance = mock_gemini_agent.return_value
        mock_agent_instance.chat_with_model = AsyncMock(return_value="feat(cli): add AI-powered commit message generation")

        mock_diff_result = MagicMock()
        mock_diff_result.stdout = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new"
        mock_diff_result.returncode = 0

        mock_staged_check_result = MagicMock()
        mock_staged_check_result.returncode = 1

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git add -A
            mock_staged_check_result, # git diff --cached --quiet
            mock_diff_result,         # git diff --cached
            MagicMock(returncode=0)   # git commit
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)
        mock_gemini_agent.assert_called_once()
        mock_agent_instance.chat_with_model.assert_awaited_once()

        commit_call = mock_run.call_args_list[3].args[0]
        self.assertIn('commit', commit_call)
        self.assertIn("feat(cli): add AI-powered commit message generation", commit_call)


    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    @patch('main.GeminiAgent')
    @patch('builtins.input', side_effect=['n', 'fix', 'test', 'Fix a bug', '', 'n', 'y'])
    def test_commit_with_generate_reject_and_manual_input(self, mock_input, mock_gemini_agent, mock_run, mock_which):
        """Test AI commit message generation is rejected and user provides manual input."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message=None,
            run_tests=False,
            generate=True
        )

        mock_agent_instance = mock_gemini_agent.return_value
        mock_agent_instance.chat_with_model = AsyncMock(return_value="feat(cli): add AI-powered commit message generation")

        mock_diff_result = MagicMock()
        mock_diff_result.stdout = "diff --git a/file.txt b/file.txt\n--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new"
        mock_diff_result.returncode = 0

        mock_staged_check_result = MagicMock()
        mock_staged_check_result.returncode = 1

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git add -A
            mock_staged_check_result, # git diff --cached --quiet
            mock_diff_result,         # git diff --cached
            MagicMock(returncode=0)   # git commit
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        commit_call = mock_run.call_args_list[3].args[0]
        self.assertIn('commit', commit_call)
        self.assertIn("fix(test): Fix a bug", commit_call)


    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    @patch('main.GeminiAgent')
    @patch('builtins.input', side_effect=['e'])
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_commit_with_generate_edit(self, mock_unlink, mock_tempfile, mock_input, mock_gemini_agent, mock_run, mock_which):
        """Test AI commit message generation is edited by the user."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message=None,
            run_tests=False,
            generate=True
        )

        mock_agent_instance = mock_gemini_agent.return_value
        mock_agent_instance.chat_with_model = AsyncMock(return_value="feat(cli): add AI-powered commit message generation")

        # Mock the temporary file to simulate user editing
        mock_tf = MagicMock()
        mock_tf.read.return_value = "feat(cli): This is an edited commit message"
        mock_tf.name = "fake_temp_file"
        mock_tempfile.return_value.__enter__.return_value = mock_tf

        mock_diff_result = MagicMock()
        mock_diff_result.stdout = "diff"
        mock_diff_result.returncode = 0

        mock_staged_check_result = MagicMock()
        mock_staged_check_result.returncode = 1

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git add -A
            mock_staged_check_result, # git diff --cached --quiet
            mock_diff_result,         # git diff --cached
            MagicMock(returncode=0),  # editor
            MagicMock(returncode=0)   # git commit
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        commit_call = mock_run.call_args_list[4].args[0]
        self.assertIn('commit', commit_call)
        self.assertIn("feat(cli): This is an edited commit message", commit_call)


    @patch('main.shutil.which', return_value='git')
    @patch('main.subprocess.run')
    @patch('main.GeminiAgent')
    @patch('builtins.input', side_effect=['feat', 'test', 'A manual commit', '', 'n', 'y'])
    def test_commit_with_generate_failure_fallback(self, mock_input, mock_gemini_agent, mock_run, mock_which):
        """Test fallback to manual input when AI generation fails."""
        args = argparse.Namespace(
            project_dir=Path("."),
            message=None,
            run_tests=False,
            generate=True
        )

        mock_agent_instance = mock_gemini_agent.return_value
        mock_agent_instance.chat_with_model = AsyncMock(side_effect=Exception("AI API is down"))

        mock_diff_result = MagicMock()
        mock_diff_result.stdout = "diff"
        mock_diff_result.returncode = 0

        mock_staged_check_result = MagicMock()
        mock_staged_check_result.returncode = 1

        mock_run.side_effect = [
            MagicMock(returncode=0),  # git add -A
            mock_staged_check_result, # git diff --cached --quiet
            mock_diff_result,         # git diff --cached
            MagicMock(returncode=0)   # git commit
        ]

        with self.assertRaises(SystemExit) as cm:
            run_commit(args)

        self.assertEqual(cm.exception.code, 0)

        commit_call = mock_run.call_args_list[3].args[0]
        self.assertIn('commit', commit_call)
        self.assertIn("feat(test): A manual commit", commit_call)


if __name__ == "__main__":
    unittest.main()
