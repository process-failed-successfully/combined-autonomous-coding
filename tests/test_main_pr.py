import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import os
import requests
import io
import sys

from main import run_pr

class TestMainPR(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)
        self.git_dir = self.project_dir / ".git"

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def _create_git_repo(self):
        self.git_dir.mkdir(exist_ok=True)

    def _run_pr_with_args(self, args):
        # Add the capture_output arg for cleaner test runs
        args._capture_output = True
        run_pr(args)

    @patch('main.load_config_from_file')
    @patch('main._pr_create')
    def test_run_pr_create_dispatch(self, mock_pr_create, mock_load_config):
        self._create_git_repo()
        mock_load_config.return_value = {"github_token": "test_token"}
        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="Test body",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )
        self._run_pr_with_args(args)
        mock_pr_create.assert_called_once()

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    @patch('subprocess.run')
    @patch('shared.github_client.GitHubClient.create_pull_request')
    def test_pr_create_success(self, mock_create_pr, mock_subprocess_run, mock_get_current_branch, mock_which, mock_load_config):
        self._create_git_repo()
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "feature-branch"
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
            self._run_pr_with_args(args)
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
        self._create_git_repo()
        mock_load_config.return_value = {}
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}, clear=True):
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
                self._run_pr_with_args(args)
            self.assertEqual(cm.exception.code, 1)

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    @patch('subprocess.run')
    def test_pr_create_branch_not_pushed(self, mock_subprocess_run, mock_get_current_branch, mock_which, mock_load_config):
        self._create_git_repo()
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "feature-branch"
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
            self._run_pr_with_args(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    def test_pr_create_on_main_branch(self, mock_get_current_branch, mock_which, mock_load_config):
        self._create_git_repo()
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "main"

        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            self._run_pr_with_args(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    def test_pr_create_no_git_executable(self, mock_which, mock_load_config):
        self._create_git_repo()
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = None

        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            self._run_pr_with_args(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.load_config_from_file')
    def test_pr_create_not_a_git_repo(self, mock_load_config):
        mock_load_config.return_value = {"github_token": "test_token"}
        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            self._run_pr_with_args(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('main.load_config_from_file')
    @patch('main.shutil.which')
    @patch('shared.git.get_current_branch')
    @patch('subprocess.run')
    @patch('shared.github_client.GitHubClient.create_pull_request')
    def test_pr_create_api_error(self, mock_create_pr, mock_subprocess_run, mock_get_current_branch, mock_which, mock_load_config):
        self._create_git_repo()
        mock_load_config.return_value = {"github_token": "test_token"}
        mock_which.return_value = "/usr/bin/git"
        mock_get_current_branch.return_value = "feature-branch"
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        mock_create_pr.side_effect = requests.exceptions.RequestException("API Error")

        args = argparse.Namespace(
            action="create",
            title="Test PR",
            body="",
            base="main",
            project_dir=self.project_dir,
            profile=None
        )

        with self.assertRaises(SystemExit) as cm:
            self._run_pr_with_args(args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
