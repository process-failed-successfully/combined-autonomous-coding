
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
mock_jira_module.JIRAError = Exception
sys.modules["jira"] = mock_jira_module

import shared.jira_client  # Ensure module is loaded for patch

class TestJiraIntegration(unittest.TestCase):

    @patch("shared.jira_client.JIRA")
    def test_jira_client_transitions(self, mock_jira_lib):
        """Test JiraClient wrapper."""
        from shared.jira_client import JiraClient
        
        # Setup Mock
        mock_instance = MagicMock()
        mock_jira_lib.return_value = mock_instance
        
        # Test Init
        config = JiraConfig(url="http://jira.local", email="user", token="token")
        client = JiraClient(config)
        
        # Test Transition
        mock_instance.transitions.return_value = [{"id": "1", "name": "In Progress"}]
        client.transition_issue("TEST-1", "In Progress")
        
        mock_instance.transition_issue.assert_called_with("TEST-1", "1")
        
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
