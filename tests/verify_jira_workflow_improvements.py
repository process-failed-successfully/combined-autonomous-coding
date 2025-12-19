
import sys
import unittest
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock jira library BEFORE importing shared.workflow
mock_jira_module = MagicMock()
class MockJIRAError(Exception):
    def __init__(self, text=None, status_code=None, **kwargs):
        super().__init__(text)
        self.status_code = status_code
mock_jira_module.JIRAError = MockJIRAError
sys.modules["jira"] = mock_jira_module

from shared.workflow import complete_jira_ticket
from shared.config import Config, JiraConfig

class TestWorkflowImprovements(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.jira = JiraConfig(url="http://jira.local", email="user", token="token", status_map={"done": "Done"})
        self.config.jira_ticket_key = "PROJ-123"
        self.config.project_dir = Path("/tmp/mock_project")

    @patch("shared.workflow.push_branch")
    @patch("shared.workflow.GitHubClient")
    @patch("shared.workflow.JiraClient")
    @patch("shared.workflow.subprocess.run")
    def test_complete_jira_ticket_with_custom_content(self, mock_subproc, mock_jira_client_class, mock_gh_client_class, mock_push):
        # Setup mocks
        mock_push.return_value = True
        
        mock_gh = MagicMock()
        mock_gh_client_class.return_value = mock_gh
        mock_gh.get_repo_info_from_remote.return_value = ("github.com", "owner", "repo")
        mock_gh.get_repo_metadata.return_value = {"default_branch": "main"}
        mock_gh.create_pr.return_value = "http://github.com/PR/1"
        
        mock_jira = MagicMock()
        mock_jira_client_class.return_value = mock_jira
        
        mock_issue = MagicMock()
        mock_jira.get_issue.return_value = mock_issue
        mock_issue.fields.comment.comments = [] # No existing comments
        
        mock_subproc.return_value.stdout = "origin_url\n"
        
        # Monkeypatch Path methods in shared.workflow
        original_exists = Path.exists
        original_read_text = Path.read_text
        
        def mock_exists(self_obj):
            if str(self_obj).endswith("PR_DESCRIPTION.md") or str(self_obj).endswith("JIRA_COMMENT.txt"):
                return True
            return False
            
        def mock_read_text(self_obj):
            if str(self_obj).endswith("PR_DESCRIPTION.md"):
                return "Custom PR Body"
            if str(self_obj).endswith("JIRA_COMMENT.txt"):
                return "Custom Jira Comment"
            return ""

        try:
            with patch.object(Path, 'exists', autospec=True, side_effect=mock_exists), \
                 patch.object(Path, 'read_text', autospec=True, side_effect=mock_read_text):
                
                # Execute
                success = asyncio.run(complete_jira_ticket(self.config))
                
                # Verify
                self.assertTrue(success)
                mock_gh.create_pr.assert_called_with(
                    "owner", "repo",
                    title="Fixes PROJ-123",
                    body="Custom PR Body",
                    head=unittest.mock.ANY,
                    base="main"
                )
                mock_jira.add_comment.assert_called_with(
                    "PROJ-123",
                    "Custom Jira Comment\nPR: http://github.com/PR/1"
                )
        finally:
            pass

    @patch("shared.workflow.push_branch")
    @patch("shared.workflow.GitHubClient")
    @patch("shared.workflow.JiraClient")
    @patch("shared.workflow.subprocess.run")
    def test_prevent_duplicate_comment(self, mock_subproc, mock_jira_client_class, mock_gh_client_class, mock_push):
        # Setup mocks
        mock_push.return_value = True
        
        mock_gh = MagicMock()
        mock_gh_client_class.return_value = mock_gh
        mock_gh.get_repo_info_from_remote.return_value = ("github.com", "owner", "repo")
        mock_gh.create_pr.return_value = "http://github.com/PR/1"
        
        mock_jira = MagicMock()
        mock_jira_client_class.return_value = mock_jira
        
        # Mock existing comment with same PR link
        mock_issue = MagicMock()
        mock_jira.get_issue.return_value = mock_issue
        mock_comment = MagicMock()
        mock_comment.body = "Already commented here http://github.com/PR/1"
        mock_issue.fields.comment.comments = [mock_comment]
        
        mock_subproc.return_value.stdout = "origin_url\n"

        def mock_exists_false(self_obj):
            return False

        with patch.object(Path, 'exists', autospec=True, side_effect=mock_exists_false):
            # Execute
            success = asyncio.run(complete_jira_ticket(self.config))
            
            # Verify
            self.assertTrue(success)
            mock_jira.add_comment.assert_not_called()

if __name__ == "__main__":
    unittest.main()
