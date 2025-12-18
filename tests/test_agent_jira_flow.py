
import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Config, JiraConfig
# Import the extracted function
from agents.gemini.agent import select_prompt

class TestAgentJiraFlow(unittest.TestCase):

    def setUp(self):
        self.config = Config(
            project_dir=Path("/tmp/test_project"),
            jira=JiraConfig(url="http://jira", email="me", token="token"),
            jira_ticket_key="TEST-1",
            jira_spec_content="TICKET CONTENT"
        )
        self.config.feature_list_path = self.config.project_dir / "feature_list.json"
        
        # Mock file system existence
        self.config.feature_list_path.exists = MagicMock(return_value=False)
        self.config.project_dir.joinpath = MagicMock()
        
    @patch("agents.gemini.agent.get_jira_initializer_prompt")
    @patch("agents.gemini.agent.get_initializer_prompt")
    def test_first_run_jira(self, mock_init, mock_jira_init):
        mock_jira_init.return_value = "JIRA_INIT"
        
        prompt, using_mgr = select_prompt(self.config, iteration=0, is_first_run=True, has_run_manager_first=False)
        
        self.assertEqual(prompt, "JIRA_INIT")
        self.assertFalse(using_mgr)
        mock_jira_init.assert_called_once()
        mock_init.assert_not_called()

    @patch("agents.gemini.agent.get_jira_initializer_prompt")
    @patch("agents.gemini.agent.get_initializer_prompt")
    def test_first_run_normal(self, mock_init, mock_jira_init):
        # Disable Jira
        self.config.jira_ticket_key = None
        mock_init.return_value = "NORMAL_INIT"
        
        prompt, using_mgr = select_prompt(self.config, iteration=0, is_first_run=True, has_run_manager_first=False)
        
        self.assertEqual(prompt, "NORMAL_INIT")
        self.assertFalse(using_mgr)
        mock_init.assert_called_once()
        mock_jira_init.assert_not_called()

    @patch("agents.gemini.agent.get_jira_manager_prompt")
    @patch("agents.gemini.agent.get_manager_prompt")
    def test_manager_run_jira(self, mock_mgr, mock_jira_mgr):
        mock_jira_mgr.return_value = "JIRA_MGR"
        # Trigger manager by frequency
        self.config.manager_frequency = 5
        
        prompt, using_mgr = select_prompt(self.config, iteration=5, is_first_run=False, has_run_manager_first=False)
        
        self.assertEqual(prompt, "JIRA_MGR")
        self.assertTrue(using_mgr)
        mock_jira_mgr.assert_called_once()
        mock_mgr.assert_not_called()

    @patch("agents.gemini.agent.get_jira_worker_prompt")
    @patch("agents.gemini.agent.get_coding_prompt")
    def test_worker_run_jira(self, mock_coding, mock_jira_worker):
        mock_jira_worker.return_value = "JIRA_WORKER"
        
        prompt, using_mgr = select_prompt(self.config, iteration=1, is_first_run=False, has_run_manager_first=False)
        
        self.assertEqual(prompt, "JIRA_WORKER")
        self.assertFalse(using_mgr)
        mock_jira_worker.assert_called_once()
        mock_coding.assert_not_called()

if __name__ == "__main__":
    unittest.main()
