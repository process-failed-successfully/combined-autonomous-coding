import unittest
from unittest.mock import patch, MagicMock, call
import argparse
import sys
from pathlib import Path

# Import the functions to test.
# We need to import main first to ensure functions are available.
import main
from main import run_pr, _pr_list, _pr_show, _pr_merge, _pr_close

class TestMainPRExtended(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.config = argparse.Namespace(
            github_token="test_token",
            github_host="github.com"
        )

    @patch('shared.github_client.GitHubClient.list_pull_requests')
    def test_pr_list(self, mock_list):
        mock_list.return_value = [
            {"number": 1, "title": "Test PR 1", "user": {"login": "user1"}, "html_url": "url1"},
            {"number": 2, "title": "Test PR 2", "user": {"login": "user2"}, "html_url": "url2"}
        ]

        args = argparse.Namespace(project_dir=self.project_dir)

        with patch('builtins.print') as mock_print:
            # Should not raise SystemExit
            _pr_list(args, self.config)

        mock_list.assert_called_with(self.project_dir)

    @patch('shared.github_client.GitHubClient.list_pull_requests')
    def test_pr_list_empty(self, mock_list):
        mock_list.return_value = []
        args = argparse.Namespace(project_dir=self.project_dir)

        with self.assertRaises(SystemExit) as cm:
            _pr_list(args, self.config)
        self.assertEqual(cm.exception.code, 0)

    @patch('shared.github_client.GitHubClient.get_pull_request')
    def test_pr_show(self, mock_get):
        mock_get.return_value = {
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "user": {"login": "user1"},
            "html_url": "url1",
            "body": "Body"
        }

        args = argparse.Namespace(project_dir=self.project_dir, number=1)

        with patch('builtins.print') as mock_print:
            _pr_show(args, self.config)

        mock_get.assert_called_with(self.project_dir, 1)

    @patch('shared.github_client.GitHubClient.merge_pull_request')
    def test_pr_merge(self, mock_merge):
        mock_merge.return_value = {"merged": True}

        args = argparse.Namespace(
            project_dir=self.project_dir,
            number=1,
            yes=True # Skip confirmation
        )

        with patch('builtins.print') as mock_print:
            _pr_merge(args, self.config)

        mock_merge.assert_called_with(self.project_dir, 1)

    @patch('shared.github_client.GitHubClient.close_pull_request')
    def test_pr_close(self, mock_close):
        mock_close.return_value = {"state": "closed"}

        args = argparse.Namespace(
            project_dir=self.project_dir,
            number=1,
            yes=True # Skip confirmation
        )

        with patch('builtins.print') as mock_print:
            _pr_close(args, self.config)

        mock_close.assert_called_with(self.project_dir, 1)

    @patch('main.load_config_from_file')
    @patch('main._pr_list')
    def test_run_pr_dispatch_list(self, mock_pr_list, mock_load_config):
        mock_load_config.return_value = {"github_token": "token"}
        args = argparse.Namespace(
            action="list",
            project_dir=self.project_dir,
            profile=None
        )
        run_pr(args)
        mock_pr_list.assert_called_once()

if __name__ == '__main__':
    unittest.main()
