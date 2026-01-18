import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys
import asyncio

# Adjust path to include the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ask import run_ask_logic
from shared.config import Config

class TestAskLogic(unittest.IsolatedAsyncioTestCase):

    @patch('shared.ask.Config')
    @patch('shared.ask.GeminiAgent')
    @patch('shared.ask.get_file_tree')
    @patch('shared.ask.get_ask_prompt')
    async def test_run_ask_logic_success(self, mock_get_ask_prompt, mock_get_file_tree, mock_GeminiAgent, mock_Config):
        # Setup mocks
        mock_config_instance = MagicMock(spec=Config)
        mock_Config.return_value = mock_config_instance

        mock_agent_instance = MagicMock()
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("done", "This is the answer.", []))
        mock_GeminiAgent.return_value = mock_agent_instance

        mock_get_file_tree.return_value = "src/\n  main.py"
        mock_get_ask_prompt.return_value = "System Prompt: Answer the question: {user_question}"

        # Test arguments
        query = "What is this?"
        project_dir = Path("/tmp/test_project")

        # Execute
        result = await run_ask_logic(query, project_dir)

        # Assertions
        self.assertTrue(result)
        mock_Config.assert_called()
        mock_GeminiAgent.assert_called_with(mock_config_instance)
        mock_agent_instance.run_agent_session.assert_called()

        # Verify prompt construction
        call_args = mock_agent_instance.run_agent_session.call_args
        prompt_passed = call_args[0][0]
        self.assertIn("What is this?", prompt_passed)
        self.assertIn("src/", prompt_passed)

    @patch('shared.ask.Config')
    @patch('shared.ask.GeminiAgent')
    async def test_run_ask_logic_with_files(self, mock_GeminiAgent, mock_Config):
        # Setup mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("done", "Answer", []))
        mock_GeminiAgent.return_value = mock_agent_instance

        # Mock file reading
        with patch('pathlib.Path.read_text', return_value="file content"):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = await run_ask_logic(
                        "Query",
                        Path("/tmp"),
                        files=["test.py"]
                    )

        self.assertTrue(result)
        prompt_passed = mock_agent_instance.run_agent_session.call_args[0][0]
        self.assertIn("--- File: test.py ---", prompt_passed)
        self.assertIn("file content", prompt_passed)

    @patch('shared.ask.Config')
    @patch('shared.ask.GeminiAgent')
    async def test_run_ask_logic_error(self, mock_GeminiAgent, mock_Config):
        # Setup mocks
        mock_agent_instance = MagicMock()
        mock_agent_instance.run_agent_session = AsyncMock(side_effect=Exception("API Error"))
        mock_GeminiAgent.return_value = mock_agent_instance

        result = await run_ask_logic("Query", Path("/tmp"))

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
