import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
from pathlib import Path
import os
import argparse

from main import run_pr

class TestMainPR(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.load_config_from_file')
    @patch('main._pr_create')
    def test_run_pr_create(self, mock_pr_create, mock_load_config):
        mock_load_config.return_value = {"github_token": "test_token"}
        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="Test body",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )
        run_pr(args)
        mock_pr_create.assert_called_once()

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    @patch('subprocess.run')
    @patch('shared.github_client.GitHubClient.create_pull_request')
    def test_pr_create_success(self, mock_create_pr, mock_subprocess_run, mock_get_current_branch, mock_which, mock_load_config):
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "feature-branch"

        # Mock for ls-remote, indicating branch is pushed
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        mock_create_pr.return_value = {"html_url": "https://github.com/user/repo/pull/1"}

        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="This is a test PR.",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            run_pr(args)
        self.assertEqual(cm.exception.code, 0)
        mock_create_pr.assert_called_once_with(
            project_dir=self.project_dir,
            title="Test PR",
            body="This is a test PR.",
            head_branch="feature-branch",
            base_branch="main"
        )

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    def test_pr_create_no_token(self, mock_get_current_branch, mock_which, mock_load_config):
        mock_load_config.return_value = {}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "feature-branch"

        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            run_pr(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    @patch('subprocess.run')
    def test_pr_create_branch_not_pushed(self, mock_subprocess_run, mock_get_current_branch, mock_which, mock_load_config):
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "feature-branch"

        # Mock for ls-remote, indicating branch is not pushed
        mock_subprocess_run.return_value = MagicMock(returncode=1)

        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            run_pr(args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
