import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from shared.config import Config
from agents.gemini.agent import GeminiAgent, run_autonomous_agent


class TestGeminiAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.project_dir = Path("/tmp/test_project")
        self.config.feature_list_path = self.config.project_dir / "features.json"
        self.config.progress_file_path = self.config.project_dir / "progress.txt"
        self.config.model = "test-model"
        self.config.max_iterations = 10
        self.config.manager_frequency = 5
        self.config.run_manager_first = False
        self.config.auto_continue_delay = 0.1
        self.config.max_consecutive_errors = 3
        self.config.login_mode = False
        self.config.verify_creation = False
        self.config.manager_model = "manager-model"
        self.config.jira = None
        self.config.jira_ticket_key = None
        self.config.jira_spec_content = None
        self.config.agent_id = "test-agent"
        self.config.bash_timeout = 120.0

        self.agent = GeminiAgent(self.config)

    @patch("agents.gemini.agent.GeminiClient")
    @patch("agents.gemini.agent.get_file_tree")
    @patch("agents.gemini.agent.process_response_blocks")
    @patch("agents.gemini.agent.get_telemetry")
    async def test_run_agent_session_basic(
        self, mock_telemetry, mock_process_blocks, mock_get_tree, mock_client_cls
    ):
        # Setup Client Mock
        mock_client_instance = mock_client_cls.return_value
        mock_client_instance.config = self.config
        mock_client_instance.run_command = AsyncMock(return_value={"content": "response"})
        mock_client_instance.agent_client = None  # default

        mock_get_tree.return_value = "file tree"
        mock_process_blocks.return_value = ("log", ["action1"])

        status, response, actions = await self.agent.run_agent_session("prompt")

        self.assertEqual(status, "continue")
        self.assertEqual(response, "response")
        self.assertEqual(actions, ["action1"])

        mock_client_instance.run_command.assert_called()
        mock_telemetry.return_value.record_histogram.assert_called()

    @patch("agents.gemini.agent.GeminiClient")
    @patch("agents.gemini.agent.get_file_tree")
    @patch("agents.gemini.agent.process_response_blocks")
    async def test_run_agent_session_error(self, mock_process_blocks, mock_get_tree, mock_client_cls):
        mock_client_instance = mock_client_cls.return_value
        mock_client_instance.config = self.config
        mock_client_instance.run_command.side_effect = Exception("Run failed")

        mock_get_tree.return_value = "file tree"

        status, response, actions = await self.agent.run_agent_session("prompt")

        self.assertEqual(status, "error")
        self.assertIn("Run failed", response)
        self.assertEqual(actions, [])

    @patch("agents.gemini.agent.GeminiClient")
    @patch("agents.gemini.agent.get_file_tree")
    async def test_run_agent_session_candidates_format(self, mock_get_tree, mock_client_cls):
        mock_client_instance = mock_client_cls.return_value
        mock_client_instance.config = self.config
        # Mock Gemini response with "candidates" format
        mock_client_instance.run_command = AsyncMock(return_value={
            "candidates": [{"content": {"parts": [{"text": "candidate text"}]}}]
        })

        with patch(
            "agents.gemini.agent.process_response_blocks", return_value=("", [])
        ):
            status, response, actions = await self.agent.run_agent_session("prompt")
            self.assertEqual(response, "candidate text")

    @patch("agents.shared.base_agent.log_startup_config")
    @patch("agents.shared.base_agent.init_telemetry")
    @patch("agents.shared.base_agent.get_telemetry")
    @patch("agents.gemini.agent.GeminiAgent.run_agent_session")
    @patch("agents.shared.base_agent.BaseAgent.select_prompt")
    @patch("agents.shared.base_agent.copy_spec_to_project")
    async def test_run_autonomous_agent_integration(
        self,
        mock_copy_spec,
        mock_select_prompt,
        mock_run_session,
        mock_get_telemetry,
        mock_init_telemetry,
        mock_log_config,
    ):
        mock_select_prompt.return_value = ("init prompt", False)
        mock_run_session.return_value = ("continue", "resp", [])

        self.config.max_iterations = 1

        # Mocking Path.exists logic that might be called during BaseAgent initialization or loop
        with patch.object(Path, "exists", return_value=False):
            await run_autonomous_agent(self.config, None)

        mock_run_session.assert_called()


if __name__ == "__main__":
    unittest.main()
