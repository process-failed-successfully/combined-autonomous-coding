import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.github_client import GitHubClient

class TestGitHubClient(unittest.TestCase):

    @patch('subprocess.run')
    def test_get_repo_owner_and_name_https(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(
            stdout="https://github.com/test-owner/test-repo.git\n",
            returncode=0
        )
        client = GitHubClient(token="fake_token")
        owner, name = client._get_repo_owner_and_name(Path("/fake/dir"))
        self.assertEqual(owner, "test-owner")
        self.assertEqual(name, "test-repo")

    @patch('subprocess.run')
    def test_get_repo_owner_and_name_ssh(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(
            stdout="git@github.com:test-owner/test-repo.git\n",
            returncode=0
        )
        client = GitHubClient(token="fake_token")
        owner, name = client._get_repo_owner_and_name(Path("/fake/dir"))
        self.assertEqual(owner, "test-owner")
        self.assertEqual(name, "test-repo")

    @patch('subprocess.run')
    def test_get_repo_owner_and_name_enterprise(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(
            stdout="https://github.my-company.com/test-owner/test-repo.git\n",
            returncode=0
        )
        client = GitHubClient(token="fake_token", host="github.my-company.com")
        owner, name = client._get_repo_owner_and_name(Path("/fake/dir"))
        self.assertEqual(owner, "test-owner")
        self.assertEqual(name, "test-repo")

    @patch('shared.github_client.requests.post')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_create_pull_request_success(self, mock_get_repo, mock_post):
        mock_get_repo.return_value = ("test-owner", "test-repo")
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "https://github.com/test-owner/test-repo/pull/1"}
        mock_post.return_value = mock_response

        client = GitHubClient(token="fake_token")
        pr = client.create_pull_request(
            project_dir=Path("/fake/dir"),
            title="Test PR",
            body="Test body",
            head_branch="feature",
            base_branch="main"
        )
        self.assertEqual(pr, {"html_url": "https://github.com/test-owner/test-repo/pull/1"})

    @patch('shared.github_client.requests.post')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_create_pull_request_failure(self, mock_get_repo, mock_post):
        mock_get_repo.return_value = ("test-owner", "test-repo")
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        client = GitHubClient(token="fake_token")
        with self.assertRaises(Exception):
            client.create_pull_request(
                project_dir=Path("/fake/dir"),
                title="Test PR",
                body="Test body",
                head_branch="feature",
                base_branch="main"
            )

if __name__ == '__main__':
    unittest.main()
