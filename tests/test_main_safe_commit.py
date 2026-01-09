import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys

# Add project root to path to allow importing main
sys.path.insert(0, str(Path(__file__).parent.parent))

import main

class TestSafeCommitCommand(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the project
        self.project_dir = Path("test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.run_format')
    @patch('main.run_lint')
    @patch('main.run_test')
    @patch('subprocess.run')
    def test_safe_commit_success(self, mock_subprocess_run, mock_run_test, mock_run_lint, mock_run_format):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit"
        )

        # Mock successful checks
        mock_run_format.return_value = None
        mock_run_lint.return_value = None
        mock_run_test.return_value = None

        # Mock git add and git diff --cached
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0), # git add -A
            MagicMock(returncode=1), # git diff --cached --quiet (changes staged)
            MagicMock(returncode=0, stdout="[main 1234567] Test commit") # git commit
        ]

        # Act and Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_safe_commit(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run_format.assert_called_once()
        mock_run_lint.assert_called_once()
        mock_run_test.assert_called_once()

        # Check git commands were called
        self.assertEqual(mock_subprocess_run.call_count, 3)
        mock_subprocess_run.assert_any_call(
            ['git', '-C', str(self.project_dir), 'add', '-A'],
            check=True, capture_output=True, text=True
        )
        mock_subprocess_run.assert_any_call(
            ['git', '-C', str(self.project_dir), 'commit', '-m', "Test commit"],
            check=True, capture_output=True, text=True
        )

    @patch('main.run_format')
    def test_safe_commit_format_fails(self, mock_run_format):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit"
        )
        # Mock format command failure
        mock_run_format.side_effect = SystemExit(1)

        # Act and Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_safe_commit(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('main.run_format')
    @patch('main.run_lint')
    def test_safe_commit_lint_fails(self, mock_run_lint, mock_run_format):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit"
        )
        mock_run_format.return_value = None
        mock_run_lint.side_effect = SystemExit(1)

        # Act and Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_safe_commit(args)

        self.assertEqual(cm.exception.code, 1)

    @patch('main.run_format')
    @patch('main.run_lint')
    @patch('main.run_test')
    def test_safe_commit_test_fails(self, mock_run_test, mock_run_lint, mock_run_format):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.project_dir,
            message="Test commit"
        )
        mock_run_format.return_value = None
        mock_run_lint.return_value = None
        mock_run_test.side_effect = SystemExit(1)

        # Act and Assert
        with self.assertRaises(SystemExit) as cm:
            main.run_safe_commit(args)

        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
