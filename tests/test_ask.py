import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ask import run_ask_logic
from shared.config import Config

class TestAskCommand(unittest.IsolatedAsyncioTestCase):

    @patch("shared.ask.setup_logger")
    @patch("shared.ask.load_config_from_file")
    @patch("shared.ask.ensure_config_exists")
    @patch("shared.ask.GeminiAgent")
    async def test_run_ask_logic_gemini(self, mock_gemini_agent, mock_ensure, mock_load_config, mock_setup_logger):
        # Setup mocks
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        mock_load_config.return_value = {}

        # Mock the agent instance and its method
        mock_agent_instance = MagicMock()
        mock_gemini_agent.return_value = mock_agent_instance

        # Async mock for run_agent_session
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("done", "The answer is 42", []))

        # Prepare arguments
        args = argparse.Namespace(
            question="What is the meaning of life?",
            project_dir=Path("."),
            agent="gemini",
            model="gemini-pro",
            verbose=False,
            profile=None
        )

        # Run logic
        await run_ask_logic(args)

        # Assertions
        mock_ensure.assert_called_once()
        mock_gemini_agent.assert_called_once()

        # Verify the prompt contained the question
        call_args = mock_agent_instance.run_agent_session.call_args
        self.assertIn("What is the meaning of life?", call_args[0][0])
        self.assertIn("INSTRUCTIONS:", call_args[0][0])

    @patch("shared.ask.setup_logger")
    @patch("shared.ask.load_config_from_file")
    @patch("shared.ask.ensure_config_exists")
    @patch("shared.ask.CursorAgent")
    async def test_run_ask_logic_cursor(self, mock_cursor_agent, mock_ensure, mock_load_config, mock_setup_logger):
        # Setup mocks
        mock_setup_logger.return_value = (MagicMock(), MagicMock())
        mock_load_config.return_value = {}

        mock_agent_instance = MagicMock()
        mock_cursor_agent.return_value = mock_agent_instance
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("done", "Cursor answer", []))

        args = argparse.Namespace(
            question="Explain main.py",
            project_dir=Path("."),
            agent="cursor",
            model=None,
            verbose=True,
            profile=None
        )

        await run_ask_logic(args)

        mock_cursor_agent.assert_called_once()
        call_args = mock_agent_instance.run_agent_session.call_args
        self.assertIn("Explain main.py", call_args[0][0])

if __name__ == '__main__':
    unittest.main()
