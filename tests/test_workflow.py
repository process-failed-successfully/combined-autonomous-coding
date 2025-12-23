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
    @patch("shared.workflow.GitHubClient")
    def test_get_remote_info_success(self, mock_gh_client_cls, mock_run):
        mock_run.return_value.stdout = "https://github.com/owner/repo.git\n"
        mock_gh_client_instance = mock_gh_client_cls.return_value
        mock_gh_client_instance.get_repo_info_from_remote.return_value = ("github.com", "owner", "repo")

        host, owner, repo = _get_remote_info(Path("/tmp"))
        self.assertEqual(host, "github.com")
        self.assertEqual(owner, "owner")
        self.assertEqual(repo, "repo")

    @patch("subprocess.run")
    def test_get_remote_info_git_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        host, owner, repo = _get_remote_info(Path("/tmp"))
        self.assertIsNone(host)

    @patch("shared.workflow._get_remote_info")
    @patch("shared.workflow.GitHubClient")
    def test_create_pr_success(self, mock_gh_client_cls, mock_get_remote):
        mock_get_remote.return_value = ("github.com", "owner", "repo")
        mock_gh_client_instance = mock_gh_client_cls.return_value
        mock_gh_client_instance.get_repo_metadata.return_value = {"default_branch": "main"}
        mock_gh_client_instance.create_pr.return_value = "http://pr-url"

        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp")
        config.jira_ticket_key = "KEY-123"

        pr_url = _create_pr(config, "feature-branch")
        self.assertEqual(pr_url, "http://pr-url")

    @patch("shared.workflow._get_remote_info")
    def test_create_pr_no_remote_info(self, mock_get_remote):
        mock_get_remote.return_value = (None, None, None)
        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp")  # Ensure this attribute exists

        pr_url = _create_pr(config, "branch")
        self.assertIsNone(pr_url)

    @patch("shared.workflow._get_remote_info")
    @patch("shared.workflow.GitHubClient")
    def test_create_pr_same_branch(self, mock_gh_client_cls, mock_get_remote):
        mock_get_remote.return_value = ("github.com", "owner", "repo")
        mock_gh_client_instance = mock_gh_client_cls.return_value
        mock_gh_client_instance.get_repo_metadata.return_value = {"default_branch": "main"}

        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp")

        pr_url = _create_pr(config, "main")
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
