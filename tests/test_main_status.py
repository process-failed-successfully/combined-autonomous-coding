import unittest
from unittest.mock import patch, MagicMock
import sys
import io
import json
from pathlib import Path
import tempfile
import shutil
import argparse

# Add project root to path to allow importing main
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main

class TestMainStatus(unittest.TestCase):
    def setUp(self):
        self.original_stdout = sys.stdout
        sys.stdout = self.captured_output = io.StringIO()
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)

        # The status command looks for logs relative to the main.py script's location
        # We need to create a predictable structure for that.
        self.mock_repo_root = self.project_path / "repo"
        self.mock_logs_dir = self.mock_repo_root / "agents/logs"
        self.mock_logs_dir.mkdir(parents=True)

        # We also need a fake main.py in our mock repo root for the path logic to work
        (self.mock_repo_root / "main.py").touch()
        self.main_file_path_patch = patch('main.__file__', str(self.mock_repo_root / "main.py"))
        self.main_file_path_patch.start()

    def tearDown(self):
        sys.stdout = self.original_stdout
        shutil.rmtree(self.test_dir)
        self.main_file_path_patch.stop()

    def run_status(self):
        """Helper to run the status command against the temp project directory."""
        args = argparse.Namespace(project_dir=self.project_path)
        # The run_status function always calls sys.exit(0)
        with self.assertRaises(SystemExit) as cm:
            main.run_status(args)
        self.assertEqual(cm.exception.code, 0)
        return self.captured_output.getvalue()

    def create_file(self, file_path, content=""):
        """Creates a file in the temporary project directory."""
        (self.project_path / file_path).write_text(content)

    @patch('subprocess.run')
    def test_status_initial_state(self, mock_subprocess_run):
        """Test status in a clean, new project."""
        # Git is not a repo
        mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="", stderr="not a repo")

        output = self.run_status()

        self.assertIn(f"--- Project Status: {self.project_path} ---", output)
        self.assertIn("🏃 In Progress", output)
        self.assertIn("No feature_list.json found.", output)
        self.assertIn("No .agent_run_id file found.", output)
        self.assertIn("Directory is not a Git repository.", output)

    @patch('subprocess.run')
    def test_status_all_markers_and_files_present_clean_git(self, mock_subprocess_run):
        """Test status with all files present and a clean git state."""
        # Git is a clean repo
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="true"), # It is a git repo
            MagicMock(returncode=0, stdout="")      # Status is clean
        ]

        # Create marker files and other artifacts
        self.create_file("PROJECT_SIGNED_OFF")
        self.create_file("feature_list.json", json.dumps(["feature 1", "feature 2"]))
        self.create_file(".agent_run_id", "test-run-123")
        (self.mock_logs_dir / "test-run-123.log").write_text("line 1\nline 2\n")

        output = self.run_status()

        # Check workflow stage
        self.assertIn("✅ Project Signed Off", output)

        # Check feature summary
        self.assertIn("Found 2 features", output)
        self.assertIn("- feature 1", output)

        # Check last run and log snippet
        self.assertIn("Last Run ID: test-run-123", output)
        self.assertIn("Log Snippet", output)
        self.assertIn("line 1", output)
        self.assertIn("line 2", output)

        # Check git status
        self.assertIn("✅ Working directory is clean.", output)

    @patch('subprocess.run')
    def test_status_qa_passed_and_dirty_git(self, mock_subprocess_run):
        """Test status for QA_PASSED stage and a dirty git state."""
        # Git is a dirty repo
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout="true"),
            MagicMock(returncode=0, stdout=" M README.md\n?? new_file.txt")
        ]

        self.create_file("QA_PASSED")

        output = self.run_status()

        self.assertIn("🤔 QA Passed", output)
        self.assertIn("Uncommitted changes detected:", output)
        self.assertIn("M README.md", output)
        self.assertIn("?? new_file.txt", output)

    def test_status_completed_stage(self):
        """Test the 'Completed' workflow stage."""
        self.create_file("COMPLETED")
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1) # Not a git repo
            output = self.run_status()
        self.assertIn("⏳ Completed", output)

if __name__ == '__main__':
    unittest.main()
