import unittest
import subprocess
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

# It's a bit of a dance to import main.py as it's a script
import sys
# Add the root of the project to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import run_experiment

class TestExperimentCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary git repository for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, check=True)
        # Create an initial commit
        (self.project_dir / "README.md").write_text("Initial commit")
        subprocess.run(["git", "add", "README.md"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _run_exp(self, *args):
        """Helper to run the experiment command with proper arguments."""
        # This is a mock for the argparse Namespace object
        base_args = {
            "project_dir": self.project_dir,
            "force": False,
            "yes": True, # Assume yes to all confirmations for automated tests
            "delete": False,
        }
        # First arg is action, the rest are specific to the action
        action = args[0]
        exp_name = args[1] if len(args) > 1 else None

        # Simulate argparse Namespace
        mock_args = MagicMock()
        mock_args.action = action
        mock_args.experiment_name = exp_name
        mock_args.project_dir = self.project_dir
        mock_args.force = False
        mock_args.yes = True
        mock_args.delete = False

        # For merge command, --delete might be passed
        if action == "merge" and "--delete" in args:
            mock_args.delete = True

        # For delete command, --force might be passed
        if action == "delete" and "--force" in args:
            mock_args.force = True

        # Redirect stdout to capture output
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                run_experiment(mock_args)
            except SystemExit as e:
                # We expect SystemExit(0) on success
                self.assertEqual(e.code, 0)
            return mock_stdout.getvalue()

    def test_start_experiment(self):
        """Test the 'experiment start' command."""
        exp_name = "test-exp-1"
        output = self._run_exp("start", exp_name)

        # Check that the worktree directory was created
        exp_path = self.project_dir / ".experiments" / exp_name
        self.assertTrue(exp_path.is_dir())

        # Check that the branch was created
        result = subprocess.run(["git", "branch", "--list"], cwd=self.project_dir, capture_output=True, text=True, check=True)
        self.assertIn(f"experiment/{exp_name}", result.stdout)

        self.assertIn(f"Successfully created experiment '{exp_name}'", output)

    def test_list_experiments(self):
        """Test the 'experiment list' command."""
        self._run_exp("start", "exp-alpha")
        self._run_exp("start", "exp-beta")

        output = self._run_exp("list")

        self.assertIn("exp-alpha", output)
        self.assertIn("exp-beta", output)

    def test_status_experiment(self):
        """Test the 'experiment status' command."""
        exp_name = "status-exp"
        self._run_exp("start", exp_name)

        # Make a change in the experiment worktree
        exp_path = self.project_dir / ".experiments" / exp_name
        (exp_path / "new_file.txt").write_text("hello")
        subprocess.run(["git", "add", "new_file.txt"], cwd=exp_path, check=True)

        output = self._run_exp("status", exp_name)

        self.assertIn(f"Status for experiment: {exp_name}", output)
        self.assertIn("new file:   new_file.txt", output)

    def test_diff_experiment(self):
        """Test the 'experiment diff' command."""
        exp_name = "diff-exp"
        self._run_exp("start", exp_name)

        exp_path = self.project_dir / ".experiments" / exp_name
        (exp_path / "diff_file.txt").write_text("some changes")
        subprocess.run(["git", "add", "diff_file.txt"], cwd=exp_path, check=True)
        subprocess.run(["git", "commit", "-m", "add diff file"], cwd=exp_path, check=True)

        output = self._run_exp("diff", exp_name)

        self.assertIn(f"Diff for experiment: {exp_name}", output)
        self.assertIn("+++ b/diff_file.txt", output)
        self.assertIn("+some changes", output)

    def test_merge_experiment(self):
        """Test the 'experiment merge' command."""
        exp_name = "merge-exp"
        self._run_exp("start", exp_name)

        exp_path = self.project_dir / ".experiments" / exp_name
        (exp_path / "merge_file.txt").write_text("merge content")
        subprocess.run(["git", "add", "merge_file.txt"], cwd=exp_path, check=True)
        subprocess.run(["git", "commit", "-m", "add merge file"], cwd=exp_path, check=True)

        # Run merge without delete first
        output = self._run_exp("merge", exp_name)

        self.assertIn("Merge successful", output)

        # Verify the file is in the main branch
        self.assertTrue((self.project_dir / "merge_file.txt").exists())

        # Check that worktree and branch still exist
        self.assertTrue(exp_path.is_dir())
        result = subprocess.run(["git", "branch", "--list"], cwd=self.project_dir, capture_output=True, text=True, check=True)
        self.assertIn(f"experiment/{exp_name}", result.stdout)

    def test_merge_and_delete_experiment(self):
        """Test merging and then deleting an experiment."""
        exp_name = "merge-delete-exp"
        self._run_exp("start", exp_name)

        exp_path = self.project_dir / ".experiments" / exp_name
        (exp_path / "merge_del_file.txt").write_text("content")
        subprocess.run(["git", "add", "."], cwd=exp_path, check=True)
        subprocess.run(["git", "commit", "-m", "commit"], cwd=exp_path, check=True)

        # Mock the delete action to check if it's called
        with patch('main._experiment_delete') as mock_delete:
            self._run_exp("merge", exp_name, "--delete")
            mock_delete.assert_called_once()

    def test_delete_experiment(self):
        """Test the 'experiment delete' command."""
        exp_name = "delete-exp"
        self._run_exp("start", exp_name)

        exp_path = self.project_dir / ".experiments" / exp_name
        self.assertTrue(exp_path.is_dir())

        output = self._run_exp("delete", exp_name)

        # Check that worktree is gone
        self.assertFalse(exp_path.exists())
        # Check that branch is gone
        result = subprocess.run(["git", "branch", "--list"], cwd=self.project_dir, capture_output=True, text=True, check=True)
        self.assertNotIn(f"experiment/{exp_name}", result.stdout)

        self.assertIn(f"Worktree for '{exp_name}' removed.", output)
        self.assertIn(f"Branch 'experiment/{exp_name}' deleted.", output)

if __name__ == '__main__':
    unittest.main()
