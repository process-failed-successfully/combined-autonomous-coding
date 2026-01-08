import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import subprocess

from main import run_pr, _get_repo_info_from_url

class TestMainPr(unittest.TestCase):

    def setUp(self):
        self.mock_project_dir = Path("/tmp/test_project")

    @patch('main.get_remote_url')
    @patch('main.get_current_branch')
    @patch('main.subprocess.run')
    @patch('main.GitHubClient')
    def test_run_pr_create_success(self, mock_github_client, mock_subprocess_run, mock_get_current_branch, mock_get_remote_url):
        # Arrange
        mock_get_remote_url.return_value = "https://github.com/test-owner/test-repo.git"
        mock_get_current_branch.return_value = "feature-branch"

        # Mock for the title commit
        mock_title_log_result = MagicMock()
        mock_title_log_result.stdout = "feat: Implement the new feature"

        # Mock for the merge base
        mock_merge_base_result = MagicMock()
        mock_merge_base_result.stdout = "abcdef123"

        # Mock for the body commits
        mock_body_log_result = MagicMock()
        mock_body_log_result.stdout = "- feat: Implement the new feature"

        mock_subprocess_run.side_effect = [
            mock_title_log_result,
            mock_merge_base_result,
            mock_body_log_result
        ]

        mock_pr_instance = mock_github_client.return_value
        mock_pr_instance.create_pull_request.return_value = {"html_url": "https://github.com/test-owner/test-repo/pull/42"}

        args = argparse.Namespace(
            project_dir=self.mock_project_dir,
            title=None,
            body=None,
            base="main"
        )

        mock_config = MagicMock()
        mock_config.github_token = "test_token"

        with patch('sys.exit') as mock_exit, patch('main.shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/git'
            with patch('pathlib.Path.exists') as mock_exists:
                mock_exists.return_value = True
                # Act
                run_pr(args, mock_config)
                # Assert
                mock_exit.assert_called_with(0)

        mock_github_client.assert_called_with(token="test_token", host="github.com")
        mock_pr_instance.create_pull_request.assert_called_with(
            owner='test-owner',
            repo='test-repo',
            title='feat: Implement the new feature',
            body='Commits for this PR:\n- feat: Implement the new feature',
            head='feature-branch',
            base='main'
        )

    @patch('main.get_remote_url')
    @patch('main.get_current_branch')
    @patch('main.subprocess.run')
    @patch('main.GitHubClient')
    def test_run_pr_create_success_enterprise(self, mock_github_client, mock_subprocess_run, mock_get_current_branch, mock_get_remote_url):
        # Arrange
        mock_get_remote_url.return_value = "https://ghe.example.com/test-owner/test-repo.git"
        mock_get_current_branch.return_value = "feature-branch"

        mock_subprocess_run.side_effect = [
            MagicMock(stdout="feat: GHE feature"),
            MagicMock(stdout="abcdef123"),
            MagicMock(stdout="- feat: GHE feature")
        ]

        mock_pr_instance = mock_github_client.return_value
        mock_pr_instance.create_pull_request.return_value = {"html_url": "https://ghe.example.com/test-owner/test-repo/pull/1"}

        args = argparse.Namespace(
            project_dir=self.mock_project_dir,
            title=None,
            body=None,
            base="main"
        )
        mock_config = MagicMock()
        mock_config.github_token = "ghe_token"

        with patch('sys.exit') as mock_exit, patch('main.shutil.which') as mock_which, \
             patch('pathlib.Path.exists', return_value=True):
            mock_which.return_value = '/usr/bin/git'
            run_pr(args, mock_config)
            mock_exit.assert_called_with(0)

        mock_github_client.assert_called_with(token="ghe_token", host="ghe.example.com")
        mock_pr_instance.create_pull_request.assert_called_with(
            owner='test-owner',
            repo='test-repo',
            title='feat: GHE feature',
            body='Commits for this PR:\n- feat: GHE feature',
            head='feature-branch',
            base='main'
        )

    def test_get_repo_info_from_url(self):
        self.assertEqual(_get_repo_info_from_url("https://github.com/owner/repo.git"), ("owner", "repo"))
        self.assertEqual(_get_repo_info_from_url("git@github.com:owner/repo.git"), ("owner", "repo"))
        self.assertEqual(_get_repo_info_from_url("https://github.com/owner/repo"), ("owner", "repo"))
        self.assertEqual(_get_repo_info_from_url("https://ghe.example.com/owner/repo"), ("owner", "repo"))
        self.assertEqual(_get_repo_info_from_url("https://gitlab.com/owner/repo"), ("owner", "repo"))


if __name__ == '__main__':
    unittest.main()
