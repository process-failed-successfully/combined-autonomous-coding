import unittest
from unittest.mock import patch, MagicMock
import sys
import io
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
        # We need a fake main.py for path logic to work if tests need it
        (self.project_path / "main.py").touch()
        self.main_file_path_patch = patch('main.__file__', str(self.project_path / "main.py"))
        self.main_file_path_patch.start()

    def tearDown(self):
        sys.stdout = self.original_stdout
        shutil.rmtree(self.test_dir)
        self.main_file_path_patch.stop()

    def run_status(self):
        """Helper to run the status command against the temp project directory."""
        args = argparse.Namespace(project_dir=self.project_path)
        with self.assertRaises(SystemExit) as cm:
            main.run_status(args)
        self.assertEqual(cm.exception.code, 0)
        return self.captured_output.getvalue()

    def create_file(self, file_path, content=""):
        """Creates a file in the temporary project directory."""
        (self.project_path / file_path).write_text(content)

    @patch('shared.cli_utils.shutil.which', return_value=None)
    def test_status_initial_state_no_git(self, mock_shutil_which):
        """Test status in a clean, new project with no git."""
        output = self.run_status()
        self.assertIn("[ Workflow: In Progress ]", output)
        self.assertIn("No agent activity recorded.", output)
        self.assertIn("Not a git repository.", output)
        self.assertIn("✅ Project is in a clean state.", output)

    @patch('shared.cli_utils.shutil.which', return_value='/usr/bin/git')
    @patch('shared.cli_utils.subprocess.run')
    def test_status_clean_git_signed_off(self, mock_subprocess_run, mock_shutil_which):
        """Test status with a clean git repo in the final workflow stage."""
        (self.project_path / ".git").mkdir()
        # subprocess.run is called by _run_enhanced_status_logic and get_suggestions
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="")

        self.create_file("PROJECT_SIGNED_OFF")
        self.create_file(".agent_history", "test-run-123-20231027120000\n")

        output = self.run_status()

        self.assertIn("[ Workflow: Signed Off ]", output)
        self.assertIn("Agent Run (test-run-123-20231027120000)", output)
        self.assertIn("✅ No uncommitted changes.", output)
        self.assertIn("`main.py clean --archive`", output)

    @patch('shared.cli_utils.shutil.which', return_value='/usr/bin/git')
    @patch('shared.cli_utils.subprocess.run')
    def test_status_dirty_git_qa_passed(self, mock_subprocess_run, mock_shutil_which):
        """Test status with a dirty git repo in the QA Passed stage."""
        (self.project_path / ".git").mkdir()
        # Important: The stdout string must exactly match what git produces
        git_output = " M README.md\n?? new_file.txt"
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout=git_output)

        self.create_file("QA_PASSED")
        output = self.run_status()

        output_lines = [line.strip() for line in output.split('\n')]

        self.assertIn("[ Workflow: QA Passed ]", output)
        self.assertIn("[ Recent File Changes ]", output)
        self.assertIn("M README.md", output_lines)
        self.assertIn("?? new_file.txt", output_lines)
        self.assertIn("[ Next Steps ]", output)
        self.assertIn("You have uncommitted changes.", output)

    @patch('shared.cli_utils.shutil.which', return_value='/usr/bin/git')
    @patch('shared.cli_utils.subprocess.run')
    def test_status_completed_stage(self, mock_subprocess_run, mock_shutil_which):
        """Test the 'Completed' workflow stage with a clean repo."""
        (self.project_path / ".git").mkdir()
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="")

        self.create_file("COMPLETED")
        output = self.run_status()
        self.assertIn("[ Workflow: Completed ]", output)
        self.assertIn("`main.py workflow advance`", output)

if __name__ == '__main__':
    unittest.main()
