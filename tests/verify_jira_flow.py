
import asyncio
import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock dependencies before importing our code
if __name__ == "__main__":
    sys.modules['shared.telemetry'] = MagicMock()
    sys.modules['shared.notifications'] = MagicMock()
    sys.modules['jira'] = MagicMock()
    sys.modules['requests'] = MagicMock()

from shared.config import Config, JiraConfig  # noqa: E402
from shared.workflow import complete_jira_ticket  # noqa: E402
from shared.utils import sanitize_url  # noqa: E402
from shared.github_client import GitHubClient  # noqa: E402


def test_sanitize_url():
    """Test that tokens are masked in URLs."""
    token_url = "https://x-access-token:ghp_123456789@github.com/owner/repo.git"
    sanitized = sanitize_url(token_url)
    assert "ghp_123456789" not in sanitized
    assert "https://****@github.com/owner/repo.git" == sanitized
    print("Verification Test Success: sanitize_url masks tokens.")


def test_ghe_api_base():
    """Test that API base is correctly set for GHE."""
    gh_com = GitHubClient(token="mock", host="github.com")
    assert gh_com.api_base_url == "https://api.github.com"

    gh_ghe = GitHubClient(token="mock", host="git.example.net")
    assert gh_ghe.api_base_url == "https://git.example.net/api/v3"
    print("Verification Test Success: GHE API base is correctly determined.")


import unittest

class TestVerifyJiraFlow(unittest.IsolatedAsyncioTestCase):
    async def test_complete_jira_ticket_success(self):
        """Test that completion flow handles git and jira calls correctly."""
        project_dir = Path("./test_project_verify")
        project_dir.mkdir(exist_ok=True)

        jira_cfg = JiraConfig(url="http://test", email="test@test", token="token")
        config = Config(
            project_dir=project_dir,
            jira=jira_cfg,
            jira_ticket_key="PROJ-123"
        )

        # Mock subprocess.run for git calls
        with patch("subprocess.run") as mock_run, \
                patch("shared.workflow.push_branch") as mock_push, \
                patch("shared.workflow.JiraClient") as mock_jira_client, \
                patch("shared.workflow.GitHubClient") as mock_gh_client, \
                patch.dict(os.environ, {"GITHUB_TOKEN": "mock_token"}):

            mock_push.return_value = True

            # Setup GitHub collaborator info
            mock_gh = MagicMock()
            mock_gh_client.return_value = mock_gh
            # get_repo_info_from_remote and get_repo_metadata are removed/replaced
            mock_gh.create_pull_request.return_value = {"html_url": "https://github.com/PR-123"}

            # Setup git remote/branch mocks
            mock_run_result = MagicMock()
            mock_run_result.stdout = "https://github.com/owner/repo.git\n"
            mock_run_result_branch = MagicMock()
            mock_run_result_branch.stdout = "agent/feature\n"
            mock_run.side_effect = [mock_run_result, mock_run_result_branch]

            # Setup Jira client
            mock_jira = MagicMock()
            mock_jira_client.return_value = mock_jira

            success = await complete_jira_ticket(config)

            self.assertTrue(success)
            mock_push.assert_called_once()
            mock_gh.create_pull_request.assert_called_once()
            mock_jira.transition_issue.assert_called_once_with("PROJ-123", "Code Review")
            mock_jira.add_comment.assert_called_once()
            print("Verification Test Success: complete_jira_ticket flows correctly.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Run simple tests
    test_sanitize_url()
    test_ghe_api_base()
    # Run unittest suite
    unittest.main()
