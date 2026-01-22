from shared.config import Config
from shared.workflow import _get_remote_info, _create_pr, complete_jira_ticket
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import subprocess

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


class TestWorkflow(unittest.IsolatedAsyncioTestCase):

    @patch("subprocess.run")
    def test_get_remote_info_success(self, mock_run):
        # This test is largely obsolete as _get_remote_info is stubbed
        # But we can verify it returns the default stub
        host, owner, repo = _get_remote_info(Path("/tmp"))
        self.assertEqual(host, "github.com")
        self.assertIsNone(owner)
        self.assertIsNone(repo)

    @patch("shared.workflow._get_remote_info")
    @patch("shared.workflow.GitHubClient")
    def test_create_pr_success(self, mock_gh_client_cls, mock_get_remote):
        import os
        mock_get_remote.return_value = ("github.com", "owner", "repo")
        mock_gh_client_instance = mock_gh_client_cls.return_value
        mock_gh_client_instance.create_pull_request.return_value = {"html_url": "http://pr-url"}

        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp")
        config.jira_ticket_key = "KEY-123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": "mock"}):
            pr_url = _create_pr(config, "feature-branch")
        self.assertEqual(pr_url, "http://pr-url")

    def test_create_pr_no_token(self):
        import os
        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp")

        with patch.dict(os.environ, {}, clear=True):
            pr_url = _create_pr(config, "branch")
        self.assertIsNone(pr_url)

    @patch("shared.workflow.JiraClient")
    @patch("shared.workflow._create_pr")
    @patch("shared.workflow.push_branch")
    @patch("subprocess.run")
    async def test_complete_jira_ticket_success(self, mock_run, mock_push, mock_create_pr, mock_jira_cls):
        config = MagicMock(spec=Config)
        config.jira = MagicMock()
        config.jira_ticket_key = "KEY-123"
        config.project_dir = Path("/tmp")

        mock_run.return_value.stdout = "current-branch\n"
        mock_push.return_value = True
        mock_create_pr.return_value = "http://pr"

        mock_jira_instance = mock_jira_cls.return_value
        mock_jira_instance.transition_issue.return_value = True
        mock_jira_instance.get_issue.return_value = None  # No existing comments

        result = await complete_jira_ticket(config)
        self.assertTrue(result)
        mock_jira_instance.add_comment.assert_called()

    @patch("subprocess.run")
    async def test_complete_jira_ticket_no_jira_config(self, mock_run):
        config = MagicMock(spec=Config)
        config.jira = None
        result = await complete_jira_ticket(config)
        self.assertFalse(result)

    @patch("subprocess.run")
    async def test_complete_jira_ticket_git_branch_fail(self, mock_run):
        config = MagicMock(spec=Config)
        config.jira = MagicMock()
        config.jira_ticket_key = "KEY-123"
        config.project_dir = Path("/tmp")

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        result = await complete_jira_ticket(config)
        self.assertFalse(result)
