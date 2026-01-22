from main import run_diff_summary
import unittest
from unittest.mock import patch, MagicMock
import io
from pathlib import Path
import argparse
import sys
import tempfile
import shutil
import subprocess

# Add the root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))


class TestDiffSummary(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        (self.project_dir / "test.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=self.project_dir, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('subprocess.run')
    def test_diff_summary_with_changes(self, mock_subprocess_run, mock_stdout):
        # Arrange
        mock_process = MagicMock()
        mock_process.stdout = " file.txt | 1 +\\n 1 file changed, 1 insertion(+)\\n"
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process

        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff_summary(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Diff Summary", output)
        self.assertIn("file.txt | 1 +", output)
        self.assertIn("1 file changed, 1 insertion(+)", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('subprocess.run')
    def test_diff_summary_no_changes(self, mock_subprocess_run, mock_stdout):
        # Arrange
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_process.returncode = 0
        mock_subprocess_run.return_value = mock_process

        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff_summary(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Diff Summary", output)
        self.assertIn("✅ No uncommitted changes.", output)

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_diff_summary_no_git(self, mock_stderr):
        # Arrange
        non_git_dir = tempfile.mkdtemp()
        args = argparse.Namespace(project_dir=Path(non_git_dir))

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff_summary(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        output = mock_stderr.getvalue()
        self.assertIn("❌ Error: Not a git repository.", output)

        shutil.rmtree(non_git_dir)


if __name__ == '__main__':
    unittest.main()
