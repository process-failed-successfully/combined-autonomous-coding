import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from shared.config import Config
from agents.cleaner.agent import run_cleaner_agent, get_cleaner_prompt

class TestCleanerAgent(unittest.TestCase):

    @patch("pathlib.Path.read_text")
    def test_get_cleaner_prompt(self, mock_read):
        mock_read.return_value = "clean things"
        prompt = get_cleaner_prompt()
        self.assertEqual(prompt, "clean things")

    @patch("agents.cleaner.agent.GeminiClient")
    @patch("agents.cleaner.agent.run_agent_session")
    async def async_test_run_cleaner_agent(self, mock_run, mock_client_cls):
        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp/test_project")

        agent_client = MagicMock()

        # Mock session return
        # Iteration 1: returns actions
        # Iteration 2: returns success, file exists check will happen
        mock_run.return_value = ("success", "response", ["action1"])

        # We need to verify loop break condition.
        # Condition 1: cleanup_report.txt exists
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [False, True] # First iter not exist, second exist

            await run_cleaner_agent(config, agent_client)

            self.assertEqual(mock_run.call_count, 2)
            agent_client.report_state.assert_any_call(current_task="Cleaning Project...")
            agent_client.report_state.assert_any_call(current_task="Cleanup Complete")

    @patch("agents.cleaner.agent.GeminiClient")
    @patch("agents.cleaner.agent.run_agent_session")
    def test_run_cleaner_agent_wrapper(self, mock_run, mock_client):
        import asyncio
        asyncio.run(self.async_test_run_cleaner_agent())

if __name__ == "__main__":
    unittest.main()
