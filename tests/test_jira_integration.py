
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Config, JiraConfig

# Mock jira library BEFORE importing shared.jira_client
# This is necessary because the jira library might not be installed in the test env
mock_jira_module = MagicMock()
class MockJIRAError(Exception):
    def __init__(self, text=None, status_code=None, **kwargs):
        super().__init__(text)
        self.status_code = status_code
mock_jira_module.JIRAError = MockJIRAError
sys.modules["jira"] = mock_jira_module
import shared.jira_client  # Ensure module is loaded for patch

class TestJiraIntegration(unittest.TestCase):

    def setUp(self):
        self.config = JiraConfig(url="http://jira.local", email="user", token="token")

    @patch("shared.jira_client.JIRA")
    def test_jira_connect(self, mock_jira_lib):
        """Test connection logic."""
        from shared.jira_client import JiraClient
        
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        mock_instance.myself.return_value = {"displayName": "Test User"}

        client = JiraClient(self.config)
        
        mock_jira_lib.assert_called_with(server="http://jira.local", basic_auth=("user", "token"))
        mock_instance.myself.assert_called_once()

    @patch("shared.jira_client.JIRA")
    def test_get_issue(self, mock_jira_lib):
        """Test fetching a single issue."""
        from shared.jira_client import JiraClient
        
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        
        client = JiraClient(self.config)
        
        # Success case
        mock_issue = MagicMock()
        mock_issue.key = "TEST-1"
        mock_instance.issue.return_value = mock_issue
        
        result = client.get_issue("TEST-1")
        self.assertEqual(result, mock_issue)
        mock_instance.issue.assert_called_with("TEST-1")

        # Not found case
        mock_instance.issue.side_effect = shared.jira_client.JIRAError(status_code=404)
        result = client.get_issue("TEST-999")
        self.assertIsNone(result)

    @patch("shared.jira_client.JIRA")
    def test_search_issues(self, mock_jira_lib):
        """Test JQL search."""
        from shared.jira_client import JiraClient
        
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        
        client = JiraClient(self.config)
        
        mock_issues = [MagicMock(), MagicMock()]
        mock_instance.search_issues.return_value = mock_issues
        
        result = client.search_issues("project = TEST")
        self.assertEqual(result, mock_issues)
        mock_instance.search_issues.assert_called_with("project = TEST", maxResults=10)

    @patch("shared.jira_client.JIRA")
    def test_get_first_todo_by_label(self, mock_jira_lib):
        """Test fetching first todo by label."""
        from shared.jira_client import JiraClient
        
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        
        client = JiraClient(self.config)
        
        mock_issue = MagicMock()
        mock_instance.search_issues.return_value = [mock_issue]
        
        result = client.get_first_todo_by_label("my-label")
        self.assertEqual(result, mock_issue)
        
        # Verify JQL construction
        call_args = mock_instance.search_issues.call_args
        jql = call_args[0][0]
        self.assertIn('labels = "my-label"', jql)
        self.assertIn('statusCategory = "To Do"', jql)
        self.assertEqual(call_args[1]['maxResults'], 1)

    @patch("shared.jira_client.JIRA")
    def test_transition_issue(self, mock_jira_lib):
        """Test JiraClient transition logic."""
        from shared.jira_client import JiraClient
        
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        
        client = JiraClient(self.config)
        
        # Mock transitions response
        mock_instance.transitions.return_value = [
            {"id": "10", "name": "In Progress"},
            {"id": "20", "name": "Done"}
        ]
        
        # Success
        success = client.transition_issue("TEST-1", "In Progress")
        self.assertTrue(success)
        mock_instance.transition_issue.assert_called_with("TEST-1", "10")
        
        # Failure - transition not found
        success = client.transition_issue("TEST-1", "Unknown Status")
        self.assertFalse(success)

    @patch("shared.jira_client.JIRA")
    def test_add_comment(self, mock_jira_lib):
        """Test adding comments."""
        from shared.jira_client import JiraClient
        
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        
        client = JiraClient(self.config)
        
        success = client.add_comment("TEST-1", "My Comment")
        self.assertTrue(success)
        mock_instance.add_comment.assert_called_with("TEST-1", "My Comment")

    @patch("shared.jira_client.JIRA")
    @patch("shared.git.subprocess.run")
    def test_repo_cloning(self, mock_subprocess, mock_jira_lib):
        """Test the logic of cloning a repo from a ticket."""
        from shared.jira_client import JiraClient
        from shared.git import clone_repo
        
        mock_subprocess.return_value.returncode = 0
        
        # Simulate Clone
        success = clone_repo("https://github.com/test/repo.git", Path("/tmp/test"))
        self.assertTrue(success)
        mock_subprocess.assert_called()
        args = mock_subprocess.call_args[0][0]
        self.assertIn("git", args)
        self.assertIn("clone", args)
        self.assertIn("https://github.com/test/repo.git", args)

if __name__ == "__main__":
    unittest.main()
