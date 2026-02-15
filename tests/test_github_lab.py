import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from io import StringIO

# Ensure we can import shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.github_lab import GitHubLabManager, run_github_lab_logic

class TestGitHubLab(unittest.TestCase):

    def setUp(self):
        self.manager = GitHubLabManager(token="fake-token")

    @patch("shared.github_lab.requests.get")
    def test_get_user(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "octocat", "name": "The Octocat"}
        mock_get.return_value = mock_response

        user = self.manager.get_user("octocat")
        self.assertEqual(user["login"], "octocat")

        # Verify URL and headers
        mock_get.assert_called_with(
            "https://api.github.com/users/octocat",
            headers={'Accept': 'application/vnd.github.v3+json', 'Authorization': 'token fake-token'},
            params=None,
            timeout=10
        )

    @patch("shared.github_lab.requests.get")
    def test_get_repo(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"full_name": "octocat/Hello-World"}
        mock_get.return_value = mock_response

        repo = self.manager.get_repo("octocat/Hello-World")
        self.assertEqual(repo["full_name"], "octocat/Hello-World")

    @patch("shared.github_lab.requests.get")
    def test_search_repos(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [{"name": "repo1"}, {"name": "repo2"}]}
        mock_get.return_value = mock_response

        results = self.manager.search_repos("python", limit=5)
        self.assertEqual(len(results), 2)
        mock_get.assert_called_with(
            "https://api.github.com/search/repositories",
            headers={'Accept': 'application/vnd.github.v3+json', 'Authorization': 'token fake-token'},
            params={"q": "python", "per_page": 5},
            timeout=10
        )

    @patch("shared.github_lab.requests.get")
    def test_get_gists(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "gist1"}]
        mock_get.return_value = mock_response

        gists = self.manager.get_gists("octocat", limit=5)
        self.assertEqual(len(gists), 1)

    @patch("shared.github_lab.requests.get")
    def test_get_tree(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"name": "file.txt", "type": "file"}]
        mock_get.return_value = mock_response

        tree = self.manager.get_tree("octocat/Hello-World", "src")
        self.assertEqual(tree[0]["name"], "file.txt")

    @patch("shared.github_lab.requests.get")
    def test_get_raw(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Hello World"
        mock_get.return_value = mock_response

        content = self.manager.get_raw("octocat/Hello-World", "README.md")
        self.assertEqual(content, "Hello World")

        # Verify custom header
        expected_headers = self.manager.headers.copy()
        expected_headers["Accept"] = "application/vnd.github.v3.raw"
        mock_get.assert_called_with(
            "https://api.github.com/repos/octocat/Hello-World/contents/README.md",
            headers=expected_headers,
            timeout=10
        )

    @patch("shared.github_lab.requests.get")
    def test_cli_integration(self, mock_get):
        # Mock user response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "octocat", "name": "The Octocat"}
        mock_get.return_value = mock_response

        args = MagicMock()
        args.action = "user"
        args.username = "octocat"
        args.token = "test-token"

        # Capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_github_lab_logic(args)
            self.assertTrue(success)
            self.assertIn("The Octocat", fake_out.getvalue())

    def test_invalid_repo_format(self):
        with self.assertRaises(ValueError):
            self.manager.get_repo("invalid-format")

if __name__ == "__main__":
    unittest.main()
