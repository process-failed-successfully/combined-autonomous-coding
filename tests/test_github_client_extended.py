import unittest
from unittest.mock import MagicMock, patch
from shared.github_client import GitHubClient
from pathlib import Path

class TestGitHubClientExtended(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.client = GitHubClient(token="test_token")

    @patch('shared.github_client.requests.get')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_list_pull_requests(self, mock_get_repo, mock_get):
        mock_get_repo.return_value = ("owner", "repo")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "title": "Test PR"}]
        mock_get.return_value = mock_response

        prs = self.client.list_pull_requests(self.project_dir)

        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["title"], "Test PR")
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls",
            headers=self.client._get_headers(),
            params={"state": "open", "per_page": 50},
            timeout=10
        )

    @patch('shared.github_client.requests.get')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_get_pull_request(self, mock_get_repo, mock_get):
        mock_get_repo.return_value = ("owner", "repo")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "title": "Test PR"}
        mock_get.return_value = mock_response

        pr = self.client.get_pull_request(self.project_dir, 1)

        self.assertEqual(pr["title"], "Test PR")
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls/1",
            headers=self.client._get_headers(),
            timeout=10
        )

    @patch('shared.github_client.requests.get')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_get_pull_request_reviews(self, mock_get_repo, mock_get):
        mock_get_repo.return_value = ("owner", "repo")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "state": "APPROVED"}]
        mock_get.return_value = mock_response

        reviews = self.client.get_pull_request_reviews(self.project_dir, 1)

        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["state"], "APPROVED")
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls/1/reviews",
            headers=self.client._get_headers(),
            timeout=10
        )

    @patch('shared.github_client.requests.get')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_get_pull_request_checks(self, mock_get_repo, mock_get):
        mock_get_repo.return_value = ("owner", "repo")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"check_runs": []}
        mock_get.return_value = mock_response

        checks = self.client.get_pull_request_checks(self.project_dir, "sha123")

        self.assertEqual(checks["check_runs"], [])
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/commits/sha123/check-runs",
            headers=self.client._get_headers(),
            timeout=10
        )

    @patch('shared.github_client.requests.put')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_merge_pull_request(self, mock_get_repo, mock_put):
        mock_get_repo.return_value = ("owner", "repo")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"merged": True}
        mock_put.return_value = mock_response

        result = self.client.merge_pull_request(self.project_dir, 1)

        self.assertTrue(result["merged"])
        mock_put.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls/1/merge",
            headers=self.client._get_headers(),
            json={"merge_method": "merge"},
            timeout=10
        )

    @patch('shared.github_client.requests.patch')
    @patch('shared.github_client.GitHubClient._get_repo_owner_and_name')
    def test_close_pull_request(self, mock_get_repo, mock_patch):
        mock_get_repo.return_value = ("owner", "repo")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"state": "closed"}
        mock_patch.return_value = mock_response

        result = self.client.close_pull_request(self.project_dir, 1)

        self.assertEqual(result["state"], "closed")
        mock_patch.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls/1",
            headers=self.client._get_headers(),
            json={"state": "closed"},
            timeout=10
        )

if __name__ == '__main__':
    unittest.main()
