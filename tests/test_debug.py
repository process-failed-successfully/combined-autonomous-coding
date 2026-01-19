
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import asyncio
from shared.debug import run_debug_logic

class TestDebugLogic(unittest.IsolatedAsyncioTestCase):
    @patch('shared.debug.asyncio.create_subprocess_exec')
    @patch('shared.debug.AgentClient')
    @patch('shared.debug.get_debug_prompt')
    async def test_run_debug_logic_success(self, mock_get_prompt, mock_agent_client, mock_exec):
        # Mock successful subprocess
        process_mock = AsyncMock()
        process_mock.stdout.readline.side_effect = [b"Success output\n", b""]
        process_mock.stderr.readline.side_effect = [b"", b""]
        process_mock.wait.return_value = 0
        mock_exec.return_value = process_mock

        result = await run_debug_logic(
            command_list=["ls", "-la"],
            project_dir=Path("/tmp"),
            agent_type="test_agent",
            model="test_model"
        )

        self.assertTrue(result)
        mock_exec.assert_called_once()
        mock_agent_client.assert_not_called()
        mock_get_prompt.assert_not_called()

    @patch('shared.debug.asyncio.create_subprocess_exec')
    @patch('shared.debug.AgentClient')
    @patch('shared.debug.get_debug_prompt')
    async def test_run_debug_logic_failure(self, mock_get_prompt, mock_agent_client, mock_exec):
        # Mock failed subprocess
        process_mock = AsyncMock()
        process_mock.stdout.readline.side_effect = [b"", b""]
        process_mock.stderr.readline.side_effect = [b"Error: File not found\n", b""]
        process_mock.wait.return_value = 1
        mock_exec.return_value = process_mock

        # Mock AgentClient
        mock_client_instance = AsyncMock()
        mock_client_instance.ask_agent.return_value = "Agent Diagnosis: Fix the path."
        mock_agent_client.return_value = mock_client_instance

        # Mock Prompt
        mock_get_prompt.return_value = "Mock Prompt Template"

        result = await run_debug_logic(
            command_list=["ls", "non_existent_file"],
            project_dir=Path("/tmp"),
            agent_type="test_agent",
            model="test_model"
        )

        self.assertFalse(result)
        mock_exec.assert_called_once()
        mock_agent_client.assert_called_once_with(agent_id="debugger")
        mock_client_instance.ask_agent.assert_awaited_once()
        mock_get_prompt.assert_called_once()

    @patch('shared.debug.asyncio.create_subprocess_exec')
    async def test_run_debug_logic_exception(self, mock_exec):
        mock_exec.side_effect = Exception("Unexpected error")

        result = await run_debug_logic(
            command_list=["ls"],
            project_dir=Path("/tmp")
        )

        self.assertFalse(result)
