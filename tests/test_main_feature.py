import unittest
from unittest.mock import patch, MagicMock, call, AsyncMock
import argparse
from pathlib import Path
import tempfile
import shutil
import subprocess
import os

from main import run_feature

class TestMainFeature(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init", "-b", "main"], cwd=self.project_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.project_dir, check=True)
        (self.project_dir / "README.md").write_text("initial commit")
        subprocess.run(["git", "add", "README.md"], cwd=self.project_dir, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.project_dir, check=True)
        (self.project_dir / "feature_file.txt").write_text("this is a new feature")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.input')
    @patch('main.run_branch')
    @patch('main.run_commit', new_callable=AsyncMock)
    @patch('main.run_push')
    @patch('main._pr_create')
    @patch('main.load_config_from_file')
    async def test_feature_workflow_full_success(self, mock_load_config, mock_pr_create, mock_push, mock_commit, mock_branch, mock_input):
        # Arrange
        mock_input.side_effect = [
            "test-feature-branch",  # Branch name
            "Implement test feature", # Commit message
            "y",                      # Confirm push
            "y",                      # Confirm PR
            "Test Feature PR Title",  # PR Title
            "This is the body.",      # PR Body
            "main"                    # Base branch
        ]
        mock_load_config.return_value = {"github_token": "test_token"}
        os.environ["GITHUB_TOKEN"] = "test_token"

        args = argparse.Namespace(project_dir=self.project_dir, profile=None)

        # Act
        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        # Assert
        self.assertEqual(cm.exception.code, 0) # Successful exit

        # Verify calls
        mock_branch.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()
        mock_pr_create.assert_called_once()

        # Check args passed to mocks
        self.assertEqual(mock_branch.call_args[0][0].branch_name, "test-feature-branch")
        self.assertEqual(mock_commit.call_args[0][0].message, "Implement test feature")
        self.assertEqual(mock_pr_create.call_args[0][0].title, "Test Feature PR Title")

    @patch('builtins.input')
    @patch('main.run_branch')
    @patch('main.run_commit', new_callable=AsyncMock)
    @patch('main.run_push')
    @patch('main._pr_create')
    async def test_feature_workflow_abort_at_push(self, mock_pr_create, mock_push, mock_commit, mock_branch, mock_input):
        # Arrange
        mock_input.side_effect = [
            "test-feature-branch",
            "Implement test feature",
            "n"  # Decline push
        ]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_branch.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_not_called()
        mock_pr_create.assert_not_called()

    @patch('builtins.input')
    @patch('main.run_branch')
    @patch('main.run_commit', new_callable=AsyncMock)
    @patch('main.run_push')
    @patch('main._pr_create')
    async def test_feature_workflow_abort_at_pr(self, mock_pr_create, mock_push, mock_commit, mock_branch, mock_input):
        # Arrange
        mock_input.side_effect = [
            "test-feature-branch",
            "Implement test feature",
            "y",  # Confirm push
            "n"   # Decline PR
        ]
        args = argparse.Namespace(project_dir=self.project_dir)

        # Act
        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_branch.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()
        mock_pr_create.assert_not_called()

    @patch('builtins.input')
    @patch('main.run_branch', side_effect=SystemExit(1))
    async def test_branch_creation_fails(self, mock_run_branch, mock_input):
        mock_input.side_effect = ["bad-branch"]
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run_branch.assert_called_once()

    @patch('builtins.input')
    @patch('main.run_branch')
    @patch('main.run_commit', new_callable=AsyncMock)
    async def test_commit_fails(self, mock_run_commit, mock_run_branch, mock_input):
        mock_input.side_effect = ["a-branch", "a-commit"]
        # Simulate failure in run_commit
        mock_run_commit.side_effect = SystemExit(1)

        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run_branch.assert_called_once()
        mock_run_commit.assert_called_once()

    @patch('builtins.input')
    @patch('main.run_branch')
    @patch('main.run_commit', new_callable=AsyncMock)
    @patch('main.run_push', side_effect=SystemExit(1))
    async def test_push_fails(self, mock_run_push, mock_run_commit, mock_run_branch, mock_input):
        mock_input.side_effect = ["a-branch", "a-commit", "y"]
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run_branch.assert_called_once()
        mock_run_commit.assert_called_once()
        mock_run_push.assert_called_once()

    @patch('builtins.input')
    @patch('main.run_branch')
    @patch('main.run_commit', new_callable=AsyncMock)
    @patch('main.run_push')
    @patch('main._pr_create', side_effect=SystemExit(1))
    @patch('main.load_config_from_file')
    async def test_pr_creation_fails(self, mock_load_config, mock_pr_create, mock_push, mock_commit, mock_branch, mock_input):
        mock_input.side_effect = ["a-branch", "a-commit", "y", "y", "title", "body", "main"]
        mock_load_config.return_value = {"github_token": "test_token"}
        os.environ["GITHUB_TOKEN"] = "test_token"
        args = argparse.Namespace(project_dir=self.project_dir, profile=None)

        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)

        self.assertEqual(cm.exception.code, 1)
        mock_branch.assert_called_once()
        mock_commit.assert_called_once()
        mock_push.assert_called_once()
        mock_pr_create.assert_called_once()

    @patch('builtins.input')
    async def test_empty_branch_name_exits(self, mock_input):
        mock_input.side_effect = [""]
        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.input')
    @patch('main.run_branch')
    async def test_empty_commit_message_exits(self, mock_run_branch, mock_input):
        mock_input.side_effect = ["my-branch", ""]
        args = argparse.Namespace(project_dir=self.project_dir)
        with self.assertRaises(SystemExit) as cm:
            await run_feature(args)
        self.assertEqual(cm.exception.code, 1)
        mock_run_branch.assert_called_once()

if __name__ == '__main__':
    unittest.main()
