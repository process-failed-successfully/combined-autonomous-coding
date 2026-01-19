import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import asyncio

# Import the function to test
from shared.commit_msg import generate_commit_message
from agents.shared.prompts import get_commit_prompt

class TestCommitMsg(unittest.IsolatedAsyncioTestCase):

    @patch("shared.commit_msg.GeminiAgent")
    @patch("shared.commit_msg.get_commit_prompt")
    async def test_generate_commit_message_success(self, mock_get_prompt, MockGeminiAgent):
        # Setup mocks
        project_dir = Path("/tmp/test_project")
        diff_content = "diff --git a/file.py b/file.py\n..."
        expected_msg = "fix(cli): fix commit message generation"

        # Mock prompt loading
        mock_get_prompt.return_value = "Generate a commit message for:\n{diff}"

        # Mock Agent
        mock_agent_instance = MockGeminiAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("DONE", expected_msg, []))

        # Execute
        result = await generate_commit_message(
            project_dir,
            diff_content,
            agent_type="gemini",
            verbose=False
        )

        # Verify
        self.assertEqual(result, expected_msg)

        # Verify Agent interaction
        MockGeminiAgent.assert_called_once()
        expected_prompt = "Generate a commit message for:\n" + diff_content
        mock_agent_instance.run_agent_session.assert_called_once_with(expected_prompt)

    @patch("shared.commit_msg.GeminiAgent")
    async def test_generate_commit_message_empty_diff(self, MockGeminiAgent):
        project_dir = Path("/tmp/test_project")
        diff_content = "   " # Empty diff

        result = await generate_commit_message(
            project_dir,
            diff_content
        )

        self.assertIsNone(result)
        MockGeminiAgent.assert_not_called()

    @patch("shared.commit_msg.GeminiAgent")
    @patch("shared.commit_msg.get_commit_prompt")
    async def test_generate_commit_message_agent_failure(self, mock_get_prompt, MockGeminiAgent):
        project_dir = Path("/tmp/test_project")
        diff_content = "some diff"

        mock_get_prompt.return_value = "{diff}"

        # Mock Agent failure
        mock_agent_instance = MockGeminiAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(side_effect=Exception("API Error"))

        result = await generate_commit_message(
            project_dir,
            diff_content
        )

        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
