import unittest
from unittest.mock import patch, MagicMock
from shared.github_client import GitHubClient

class TestGitHubClient(unittest.TestCase):

    @patch('shared.github_client.requests.post')
    def test_create_pull_request_success(self, mock_post):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "https://github.com/owner/repo/pull/1"}
        mock_post.return_value = mock_response

        client = GitHubClient(token="test_token")

        # Act
        pr = client.create_pull_request(
            owner="owner",
            repo="repo",
            title="Test PR",
            body="This is a test.",
            head="feature-branch",
            base="main"
        )

        # Assert
        self.assertEqual(pr["html_url"], "https://github.com/owner/repo/pull/1")
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        self.assertIn("https://api.github.com/repos/owner/repo/pulls", call_args)
        self.assertIn('"title": "Test PR"', call_kwargs['data'])

    @patch('shared.github_client.requests.post')
    def test_create_pull_request_enterprise(self, mock_post):
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"html_url": "https://ghe.example.com/owner/repo/pull/1"}
        mock_post.return_value = mock_response

        client = GitHubClient(token="test_token", host="ghe.example.com")

        # Act
        client.create_pull_request(
            owner="owner",
            repo="repo",
            title="Test PR",
            body="This is a test.",
            head="feature-branch",
            base="main"
        )

        # Assert
        mock_post.assert_called_once()
        call_args, call_kwargs = mock_post.call_args
        self.assertIn("https://ghe.example.com/api/v3/repos/owner/repo/pulls", call_args)

    def test_token_missing(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                GitHubClient(token=None)

if __name__ == '__main__':
    unittest.main()
