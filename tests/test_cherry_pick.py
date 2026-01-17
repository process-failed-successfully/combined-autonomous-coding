import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import os
import sys

# Add the root of the project to the Python path
# This is necessary for the tests to be able to import the 'shared' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.git_commands.cherry_pick import run_cherry_pick, _find_commit_by_run_id

class TestCherryPickCommand(unittest.TestCase):
    def setUp(self):
        """Set up a temporary git repository for testing."""
        self.test_dir = Path("test_repo_cherry_pick")
        self.test_dir.mkdir(exist_ok=True)

        subprocess.run(["git", "init", "-b", "main"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True)

        # Create the first commit on 'main'
        (self.test_dir / "file1.txt").write_text("Initial content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.test_dir, check=True)

        # Create a feature branch and a commit to be cherry-picked
        subprocess.run(["git", "checkout", "-b", "feature"], cwd=self.test_dir, check=True)
        (self.test_dir / "file2.txt").write_text("Feature content")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        run_id = "run-12345"
        subprocess.run(["git", "commit", "-m", f"feat: Add file2\n\nRun ID: {run_id}"], cwd=self.test_dir, check=True)
        self.cherry_pick_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
            text=True
        ).stdout.strip()

        # Create a commit that will cause a conflict
        (self.test_dir / "file1.txt").write_text("Feature branch modification")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "feat: Modify file1 on feature"], cwd=self.test_dir, check=True)
        self.conflict_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
            text=True
        ).stdout.strip()

        # Switch back to main and make a conflicting change
        subprocess.run(["git", "checkout", "main"], cwd=self.test_dir, check=True)
        (self.test_dir / "file1.txt").write_text("Main branch modification")
        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Modify file1 on main"], cwd=self.test_dir, check=True)

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    @patch('sys.stdout')
    def test_cherry_pick_successful(self, mock_stdout):
        """Test a successful cherry-pick operation using a commit hash."""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = self.cherry_pick_commit

        with self.assertRaises(SystemExit) as cm:
            run_cherry_pick(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.test_dir / "file2.txt").exists())
        self.assertEqual((self.test_dir / "file2.txt").read_text(), "Feature content")

    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_cherry_pick_with_run_id(self, mock_stderr, mock_stdout):
        """Test successfully resolving the commit from a Run ID."""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = "run-12345" # This ID is in the commit message

        with self.assertRaises(SystemExit) as cm:
            run_cherry_pick(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue((self.test_dir / "file2.txt").exists())

    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_cherry_pick_conflict(self, mock_stderr, mock_stdout):
        """Test a cherry-pick operation that results in a merge conflict."""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = self.conflict_commit

        with self.assertRaises(SystemExit) as cm:
            run_cherry_pick(args)

        self.assertEqual(cm.exception.code, 1)

        # Check that the error message contains instructions for the user
        stderr_output = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
        self.assertIn("Error: Cherry-pick failed.", stderr_output)
        self.assertIn("Please resolve the conflicts", stderr_output)
        self.assertIn("git cherry-pick --continue", stderr_output)
        self.assertIn("git cherry-pick --abort", stderr_output)

        # Verify that the repository is in a conflicted state
        git_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.test_dir,
            capture_output=True,
            text=True
        ).stdout
        self.assertIn("UU file1.txt", git_status)

    @patch('sys.stdout')
    @patch('sys.stderr')
    def test_cherry_pick_security_invalid_target(self, mock_stderr, mock_stdout):
        """Test that cherry-pick rejects invalid targets (starting with -)."""
        args = MagicMock()
        args.project_dir = self.test_dir
        args.target = "-invalid-flag"

        with self.assertRaises(SystemExit) as cm:
            run_cherry_pick(args)

        self.assertEqual(cm.exception.code, 1)

        # Verify stderr message
        stderr_output = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
        self.assertIn("Error: Invalid git reference", stderr_output)

    @patch('shared.git_commands.cherry_pick.subprocess.run')
    def test_find_commit_by_run_id_uses_fixed_strings(self, mock_run):
        """Test that _find_commit_by_run_id uses --fixed-strings to prevent regex injection."""
        project_dir = Path("/tmp/test_project")
        git_path = "/usr/bin/git"
        run_id = "run-123"

        # Mock the return value for subprocess.run
        mock_run.return_value.stdout = "commit_hash\n"
        mock_run.return_value.returncode = 0

        _find_commit_by_run_id(project_dir, git_path, run_id)

        # Verify that subprocess.run was called with the correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("--fixed-strings", call_args)

        # Check that --grep and the value are separate arguments
        self.assertIn("--grep", call_args)
        self.assertIn(f"Run ID: {run_id}", call_args)

        # Ensure they are adjacent
        grep_index = call_args.index("--grep")
        self.assertEqual(call_args[grep_index + 1], f"Run ID: {run_id}")

if __name__ == '__main__':
    unittest.main()
