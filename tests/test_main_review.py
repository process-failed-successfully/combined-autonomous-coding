
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import sys
import os

# Adjust the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_review

class TestReviewCommand(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".agent_history").write_text("run123\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.shutil.which')
    @patch('main.subprocess.run')
    @patch('builtins.print')
    def test_run_review_success(self, mock_print, mock_subprocess_run, mock_shutil_which):
        # Arrange
        mock_shutil_which.return_value = "/usr/bin/git"
        (self.project_dir / ".git").mkdir()
        (self.project_dir / "final_metrics.txt").write_text("Run ID: run123\nTotal Iterations: 5\n")
        (self.project_dir / "qa_summary.txt").write_text("QA Passed\n")
        (self.project_dir / "reviewer_report.txt").write_text("Looks good\n")

        # Mock subprocess calls
        mock_subprocess_run.side_effect = [
            # git log call
            MagicMock(stdout="a1b2c3d4e5f6\n", returncode=0, check=True),
            # git show --stat call
            MagicMock(stdout="... 1 file changed, 2 insertions(+), 1 deletion(-)\n", returncode=0, check=True),
        ]

        args = MagicMock(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_print.assert_any_call("Last Run ID: run123")
        mock_print.assert_any_call("Found 1 commit(s) for this run:")
        mock_print.assert_any_call("\n--- Commit: a1b2c3d ---")
        mock_print.assert_any_call("  Total Iterations : 5")
        mock_print.assert_any_call("QA Passed")
        mock_print.assert_any_call("Looks good")


    @patch('builtins.print')
    def test_run_review_no_history(self, mock_print):
        # Arrange
        (self.project_dir / ".agent_history").unlink()
        args = MagicMock(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_review(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("No agent run history found for this project.")

if __name__ == '__main__':
    unittest.main()
