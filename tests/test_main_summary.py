import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import shutil
from pathlib import Path
import subprocess
import io
import contextlib

# It's better to add the project root to the path if necessary,
# but for this structure, direct import should work if run with `run_tests.sh`.
import main

class TestMainSummary(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # Create a mock .git directory to simulate a git repo
        (self.project_dir / ".git").mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_summary_and_capture_output(self):
        """Helper to run the summary command and capture its stdout."""
        args = MagicMock()
        args.project_dir = self.project_dir

        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            with self.assertRaises(SystemExit):
                main.run_summary(args)

        return stdout_capture.getvalue()

    @patch("main.shutil.which", return_value="/usr/bin/git")
    @patch("main.subprocess.run")
    def test_summary_clean_repo_in_progress(self, mock_subprocess_run, mock_which):
        """Test summary for a clean repo in the 'In Progress' stage."""
        # Mock git status to show a clean 'main' branch
        mock_subprocess_run.return_value = MagicMock(
            stdout="## main...origin/main\n",
            stderr="",
            returncode=0
        )

        output = self._run_summary_and_capture_output()

        self.assertIn(f"--- Project Summary: {self.project_dir} ---", output)
        self.assertIn("  Workflow Stage      : In Progress", output)
        self.assertIn("  Key Artifacts       : None", output)
        self.assertIn("  Git Branch          : main", output)
        self.assertIn("  Git Status          : Clean", output)
        self.assertIn("  Last Activity       : No agent runs recorded.", output)

    @patch("main.shutil.which", return_value="/usr/bin/git")
    @patch("main.subprocess.run")
    def test_summary_with_changes_and_artifacts(self, mock_subprocess_run, mock_which):
        """Test summary with uncommitted changes and some artifacts."""
        # Create mock artifacts and history
        (self.project_dir / "feature_list.json").touch()
        (self.project_dir / "reviewer_report.txt").touch()
        with open(self.project_dir / ".agent_history", "w") as f:
            f.write("run_123\n")
            f.write("run_456\n")

        # Mark workflow as COMPLETED
        (self.project_dir / "COMPLETED").touch()

        # Mock git status to show 2 uncommitted changes on 'feature-branch'
        mock_subprocess_run.return_value = MagicMock(
            stdout="## feature-branch\nM  file1.py\n?? new_file.txt\n",
            stderr="",
            returncode=0
        )

        output = self._run_summary_and_capture_output()

        self.assertIn("  Workflow Stage      : Completed", output)
        self.assertIn("  Key Artifacts       : Feature Plan, Reviewer Report", output)
        self.assertIn("  Git Branch          : feature-branch", output)
        self.assertIn("  Git Status          : 2 uncommitted change(s)", output)
        self.assertIn("  Last Run ID         : run_456", output)

    @patch("main.shutil.which", return_value="/usr/bin/git")
    @patch("main.subprocess.run")
    def test_summary_qa_passed_stage(self, mock_subprocess_run, mock_which):
        """Test summary for the 'QA Passed' stage."""
        (self.project_dir / "QA_PASSED").touch()

        mock_subprocess_run.return_value = MagicMock(stdout="## main\n", returncode=0)
        output = self._run_summary_and_capture_output()
        self.assertIn("  Workflow Stage      : QA Passed", output)

    @patch("main.shutil.which", return_value="/usr/bin/git")
    @patch("main.subprocess.run")
    def test_summary_signed_off_stage(self, mock_subprocess_run, mock_which):
        """Test summary for the 'Signed Off' stage."""
        (self.project_dir / "PROJECT_SIGNED_OFF").touch()

        mock_subprocess_run.return_value = MagicMock(stdout="## main\n", returncode=0)
        output = self._run_summary_and_capture_output()
        self.assertIn("  Workflow Stage      : Signed Off", output)

    @patch("main.shutil.which", return_value=None) # Mock git not being found
    def test_summary_not_a_git_repo(self, mock_which):
        """Test summary when the directory is not a git repository."""
        # Remove the .git dir created in setUp
        shutil.rmtree(self.project_dir / ".git")

        output = self._run_summary_and_capture_output()
        self.assertIn("  Git Status          : Not a git repository.", output)
        # Ensure other fields still print
        self.assertIn("  Workflow Stage      : In Progress", output)

    @patch("main.shutil.which", return_value="/usr/bin/git")
    @patch("main.subprocess.run")
    def test_summary_git_status_error(self, mock_subprocess_run, mock_which):
        """Test summary when the git command fails."""
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "git", stderr="fatal error")

        output = self._run_summary_and_capture_output()
        self.assertIn("  Git Status          : Error checking status", output)

    @patch("main.shutil.which", return_value="/usr/bin/git")
    @patch("main.subprocess.run")
    def test_summary_empty_history_file(self, mock_subprocess_run, mock_which):
        """Test summary when the history file exists but is empty."""
        (self.project_dir / ".agent_history").touch()
        mock_subprocess_run.return_value = MagicMock(stdout="## main\n", returncode=0)

        output = self._run_summary_and_capture_output()
        self.assertIn("  Last Activity       : No runs in history.", output)

if __name__ == '__main__':
    unittest.main()
