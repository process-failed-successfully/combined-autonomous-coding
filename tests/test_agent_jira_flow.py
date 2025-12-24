
import unittest
from unittest.mock import patch, PropertyMock
import sys
from pathlib import Path
import tempfile
import shutil

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import Config, JiraConfig  # noqa: E402
from agents.gemini.agent import GeminiAgent  # noqa: E402

class TestAgentJiraFlow(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config = Config(
            project_dir=Path(self.tmp_dir),
            jira=JiraConfig(url="http://jira", email="me", token="token"),
            jira_ticket_key="TEST-1",
            jira_spec_content="TICKET CONTENT"
        )

        # Patch the property on the class
        self.flp_patcher = patch("shared.config.Config.feature_list_path", new_callable=PropertyMock)
        self.mock_flp = self.flp_patcher.start()
        # Default behavior: exists returns False
        self.mock_flp.return_value.exists.return_value = False

        self.addCleanup(self.flp_patcher.stop)
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))

    @patch("agents.shared.prompts.get_jira_initializer_prompt")
    @patch("agents.shared.prompts.get_initializer_prompt")
    def test_first_run_jira(self, mock_init, mock_jira_init):
        mock_jira_init.return_value = "JIRA_INIT"

        agent = GeminiAgent(self.config)
        agent.iteration = 0
        agent.is_first_run = True
        agent.has_run_manager_first = False

        prompt, using_mgr = agent.select_prompt()

        self.assertEqual(prompt, "JIRA_INIT")
        self.assertFalse(using_mgr)
        mock_jira_init.assert_called_once()
        mock_init.assert_not_called()

    @patch("agents.shared.prompts.get_jira_initializer_prompt")
    @patch("agents.shared.prompts.get_initializer_prompt")
    def test_first_run_normal(self, mock_init, mock_jira_init):
        # Disable Jira
        self.config.jira_ticket_key = None
        mock_init.return_value = "NORMAL_INIT"

        agent = GeminiAgent(self.config)
        agent.iteration = 0
        agent.is_first_run = True
        agent.has_run_manager_first = False

        prompt, using_mgr = agent.select_prompt()

        self.assertEqual(prompt, "NORMAL_INIT")
        self.assertFalse(using_mgr)
        mock_init.assert_called_once()
        mock_jira_init.assert_not_called()

    @patch("agents.shared.prompts.get_jira_manager_prompt")
    @patch("agents.shared.prompts.get_manager_prompt")
    def test_manager_run_jira(self, mock_mgr, mock_jira_mgr):
        mock_jira_mgr.return_value = "JIRA_MGR"
        
        # Create TRIGGER_MANAGER file to bypass QA logic
        (self.config.project_dir / "TRIGGER_MANAGER").touch()

        agent = GeminiAgent(self.config)
        agent.iteration = 5
        agent.is_first_run = False
        agent.has_run_manager_first = False

        prompt, using_mgr = agent.select_prompt()

        self.assertEqual(prompt, "JIRA_MGR")
        self.assertTrue(using_mgr)
        mock_jira_mgr.assert_called_once()
        mock_mgr.assert_not_called()

    @patch("agents.shared.prompts.get_jira_worker_prompt")
    @patch("agents.shared.prompts.get_coding_prompt")
    def test_worker_run_jira(self, mock_coding, mock_jira_worker):
        mock_jira_worker.return_value = "JIRA_WORKER"

        agent = GeminiAgent(self.config)
        agent.iteration = 1
        agent.is_first_run = False
        agent.has_run_manager_first = False

        prompt, using_mgr = agent.select_prompt()

        self.assertEqual(prompt, "JIRA_WORKER")
        self.assertFalse(using_mgr)
        mock_jira_worker.assert_called_once()
        mock_coding.assert_not_called()


if __name__ == "__main__":
    unittest.main()
