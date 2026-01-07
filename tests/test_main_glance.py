
import unittest
from unittest.mock import patch, MagicMock, ANY
from pathlib import Path
import tempfile
import argparse
import io
from contextlib import redirect_stdout

from main import run_glance

class TestMainGlance(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        (self.project_dir / ".git").mkdir()  # Simulate a git repo

        # Mock args
        self.args = argparse.Namespace(project_dir=self.project_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('main.get_workflow_stage', return_value='IN_PROGRESS')
    def test_glance_clean_state(self, mock_get_stage, mock_which, mock_run, mock_get_suggestions):
        # Arrange: Clean git status, one suggestion
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        mock_get_suggestions.return_value = [{'command': 'main.py --spec your_spec.txt'}]

        # Act
        f = io.StringIO()
        with redirect_stdout(f):
            run_glance(self.args)
        output = f.getvalue()

        # Assert
        self.assertIn("--- Project Glance", output)
        self.assertIn("Stage", output)
        self.assertIn("In Progress", output)
        self.assertIn("Git Status", output)
        self.assertIn("✅ Clean", output)
        self.assertIn("Next Step", output)
        self.assertIn("`main.py --spec your_spec.txt`", output)
        mock_get_suggestions.assert_called_once_with(self.project_dir, limit=1)

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('main.get_workflow_stage', return_value='COMPLETED')
    def test_glance_with_uncommitted_changes(self, mock_get_stage, mock_which, mock_run, mock_get_suggestions):
        # Arrange: Git status with staged, unstaged, and untracked files
        git_status_output = (
            "M  module/file1.py\n"
            " D module/file2.py\n"
            "?? new_file.txt\n"
        )
        mock_run.return_value = MagicMock(stdout=git_status_output, returncode=0)
        mock_get_suggestions.return_value = [{'command': 'main.py diff-summary'}]

        # Act
        f = io.StringIO()
        with redirect_stdout(f):
            run_glance(self.args)
        output = f.getvalue()

        # Assert
        self.assertIn("--- Project Glance", output)
        self.assertIn("Stage", output)
        self.assertIn("Completed", output)
        self.assertIn("Git Status", output)
        self.assertIn("⚠️ 1 staged, 1 unstaged, 1 untracked", output)
        self.assertIn("Next Step", output)
        self.assertIn("`main.py diff-summary`", output)

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    @patch('shutil.which', return_value='/usr/bin/git')
    @patch('main.get_workflow_stage', return_value='IN_PROGRESS')
    def test_glance_with_mixed_changes(self, mock_get_stage, mock_which, mock_run, mock_get_suggestions):
        # Arrange: Git status with a file that is both staged and unstaged ('MM')
        git_status_output = "MM module/file1.py\n"
        mock_run.return_value = MagicMock(stdout=git_status_output, returncode=0)
        mock_get_suggestions.return_value = [{'command': 'main.py diff-summary'}]

        # Act
        f = io.StringIO()
        with redirect_stdout(f):
            run_glance(self.args)
        output = f.getvalue()

        # Assert
        self.assertIn("--- Project Glance", output)
        self.assertIn("Git Status", output)
        self.assertIn("⚠️ 1 staged, 1 unstaged", output)

    @patch('main.get_suggestions')
    @patch('subprocess.run')
    @patch('shutil.which', return_value=None) # Git not found
    @patch('main.get_workflow_stage', return_value='QA_PASSED')
    def test_glance_no_git(self, mock_get_stage, mock_which, mock_run, mock_get_suggestions):
        # Arrange
        mock_get_suggestions.return_value = [{'command': 'main.py workflow advance'}]

        # Act
        f = io.StringIO()
        with redirect_stdout(f):
            run_glance(self.args)
        output = f.getvalue()

        # Assert
        self.assertIn("--- Project Glance", output)
        self.assertIn("Stage", output)
        self.assertIn("QA Passed", output)
        self.assertIn("Git Status", output)
        self.assertIn("Git not found", output)
        self.assertIn("Next Step", output)
        self.assertIn("`main.py workflow advance`", output)
        mock_run.assert_not_called() # subprocess.run should not be called if git is not found

if __name__ == '__main__':
    unittest.main()
