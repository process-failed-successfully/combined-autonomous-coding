from shared.github_client import GitHubClient
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


class TestGitHubClient(unittest.TestCase):

    def setUp(self):
        self.token = "fake_token"
        self.client = GitHubClient(token=self.token)

    def test_init_defaults(self):
        client = GitHubClient(token="token")
        self.assertEqual(client.api_base, "https://api.github.com")

    def test_init_enterprise(self):
        client = GitHubClient(token="token", host="github.enterprise.com")
        self.assertEqual(client.api_base, "https://github.enterprise.com/api/v3")

    @patch("requests.get")
    def test_get_repo_metadata_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "repo", "default_branch": "main"}
        mock_get.return_value = mock_response

        meta = self.client.get_repo_metadata("owner", "repo")
        self.assertEqual(meta["name"], "repo")
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_repo_metadata_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        meta = self.client.get_repo_metadata("owner", "repo")
        self.assertIsNone(meta)

    @patch("requests.get")
    def test_get_repo_metadata_exception(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        meta = self.client.get_repo_metadata("owner", "repo")
        self.assertIsNone(meta)

    @patch("requests.post")
    def test_create_pr_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "http://github.com/owner/repo/pull/1"}
        mock_post.return_value = mock_response

        url = self.client.create_pr("owner", "repo", "Title", "Body", "feature")
        self.assertEqual(url, "http://github.com/owner/repo/pull/1")

    @patch("requests.post")
    def test_create_pr_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        url = self.client.create_pr("owner", "repo", "Title", "Body", "feature")
        self.assertIsNone(url)

    def test_create_pr_no_token(self):
        client = GitHubClient(token="")
        # Force token to empty just in case env var is set
        client.token = ""
        url = client.create_pr("owner", "repo", "Title", "Body", "feature")
        self.assertIsNone(url)

    def test_get_repo_info_from_remote_https(self):
        url = "https://github.com/owner/repo.git"
        host, owner, repo = self.client.get_repo_info_from_remote(url)
        self.assertEqual(host, "github.com")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")

    def test_get_repo_info_from_remote_ssh(self):
        url = "git@github.com:owner/repo.git"
        host, owner, repo = self.client.get_repo_info_from_remote(url)
        self.assertEqual(host, "github.com")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")

    def test_get_repo_info_from_remote_invalid(self):
        url = "invalid_url"
        host, owner, repo = self.client.get_repo_info_from_remote(url)
        self.assertIsNone(host)
