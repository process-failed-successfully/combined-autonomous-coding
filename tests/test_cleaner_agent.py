import unittest
from unittest.mock import patch, MagicMock
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
    @patch("agents.cleaner.agent.run_gemini_session")
    async def async_test_run_cleaner_agent_gemini(self, mock_run, mock_client_cls):
        from unittest.mock import AsyncMock
        mock_run.side_effect = AsyncMock(return_value=("success", "response", ["action1"]))
        
        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp/test_project")
        config.agent_type = "gemini"

        agent_client = MagicMock()

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [False, True]

            await run_cleaner_agent(config, agent_client)

            self.assertEqual(mock_run.call_count, 2)
            agent_client.report_state.assert_any_call(current_task="Cleaning Project...")
            agent_client.report_state.assert_any_call(current_task="Cleanup Complete")

    @patch("agents.cleaner.agent.GeminiClient")
    @patch("agents.cleaner.agent.run_gemini_session")
    def test_run_cleaner_agent_gemini(self, mock_run, mock_client):
        import asyncio
        asyncio.run(self.async_test_run_cleaner_agent_gemini())

    @patch("agents.cleaner.agent.GeminiClient")
    async def async_test_run_cleaner_agent_cursor(self, mock_gemini_client):
        from unittest.mock import AsyncMock
        config = MagicMock(spec=Config)
        config.project_dir = Path("/tmp/test_project")
        config.agent_type = "cursor"

        agent_client = MagicMock()
        
        mock_cursor_client = MagicMock()
        mock_run_cursor = AsyncMock(return_value=("success", "response", []))

        with patch("agents.cursor.client.CursorClient", return_value=mock_cursor_client, create=True):
            with patch("agents.cursor.agent.run_agent_session", mock_run_cursor, create=True):
                with patch.object(Path, "exists", return_value=True):
                    await run_cleaner_agent(config, agent_client)
        
        mock_run_cursor.assert_called_once()
        self.assertEqual(config.agent_type, "cursor")

    def test_run_cleaner_agent_cursor(self):
        import asyncio
        asyncio.run(self.async_test_run_cleaner_agent_cursor())


if __name__ == "__main__":
    unittest.main()
