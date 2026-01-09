import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import tempfile
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import parse_args, run_diff

class TestDiffCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.git_path = shutil.which("git")
        if not self.git_path:
            self.fail("Git executable not found in PATH")

        # Initialize a git repository
        subprocess.run([self.git_path, "init", "-b", "main"], cwd=self.project_dir, capture_output=True)
        subprocess.run([self.git_path, "config", "user.name", "Test User"], cwd=self.project_dir)
        subprocess.run([self.git_path, "config", "user.email", "test@example.com"], cwd=self.project_dir)


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.subprocess.run')
    def test_diff_uncommitted_changes(self, mock_subprocess_run):
        # Arrange
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        args = parse_args(['diff', '--project-dir', str(self.project_dir)])

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_once()
        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn("diff", called_args)
        self.assertIn("HEAD", called_args)

    @patch('main._find_commit_by_run_id')
    @patch('main.subprocess.run')
    def test_diff_with_run_id(self, mock_subprocess_run, mock_find_commit):
        # Arrange
        run_id = "test-run-123"
        commit_hash = "abcdef123456"
        mock_find_commit.return_value = commit_hash

        # Mock the git rev-parse check to fail, forcing a lookup by Run ID
        mock_rev_parse = MagicMock()
        mock_rev_parse.returncode = 1
        # Mock the final 'git show' call
        mock_show = MagicMock()
        mock_show.returncode = 0
        mock_subprocess_run.side_effect = [mock_rev_parse, mock_show]

        args = parse_args(['diff', run_id, '--project-dir', str(self.project_dir)])

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_find_commit.assert_called_once_with(self.project_dir, self.git_path, run_id)

        self.assertEqual(mock_subprocess_run.call_count, 2)
        show_call_args = mock_subprocess_run.call_args_list[1][0][0]
        self.assertIn("show", show_call_args)
        self.assertIn(commit_hash, show_call_args)

    @patch('main.subprocess.run')
    def test_diff_with_commit_hash(self, mock_subprocess_run):
        # Arrange
        commit_hash = "abcdef123456"

        # Mock the git rev-parse check to succeed
        mock_rev_parse = MagicMock()
        mock_rev_parse.returncode = 0
        # Mock the final 'git show' call
        mock_show = MagicMock()
        mock_show.returncode = 0
        mock_subprocess_run.side_effect = [mock_rev_parse, mock_show]

        args = parse_args(['diff', commit_hash, '--project-dir', str(self.project_dir)])

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_subprocess_run.call_count, 2)
        show_call_args = mock_subprocess_run.call_args_list[1][0][0]
        self.assertIn("show", show_call_args)
        self.assertIn(commit_hash, show_call_args)

    @patch('main._find_commit_by_run_id')
    @patch('main.subprocess.run')
    def test_diff_invalid_target(self, mock_subprocess_run, mock_find_commit):
        # Arrange
        invalid_target = "non-existent-target"
        mock_find_commit.return_value = None

        # Mock the git rev-parse check to fail
        mock_rev_parse = MagicMock()
        mock_rev_parse.returncode = 1
        mock_subprocess_run.return_value = mock_rev_parse

        args = parse_args(['diff', invalid_target, '--project-dir', str(self.project_dir)])

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        mock_find_commit.assert_called_once_with(self.project_dir, self.git_path, invalid_target)

if __name__ == '__main__':
    unittest.main()
