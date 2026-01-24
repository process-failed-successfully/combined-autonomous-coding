import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import argparse
from shared.explain import run_explain_logic

class TestExplain(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.args = argparse.Namespace(
            project_dir=Path("/tmp/project"),
            file=["test_file.py"],
            detail="high",
            diagram=False,
            agent="gemini",
            model="gemini-1.5-pro",
            verbose=False
        )

    @patch("shared.explain.Config")
    @patch("shared.explain.GeminiAgent")
    @patch("shared.explain.get_explain_prompt")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.read_text")
    async def test_run_explain_logic_success(self, mock_read_text, mock_is_file, mock_exists, mock_get_prompt, MockAgent, MockConfig):
        # Setup mocks
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read_text.return_value = "print('hello world')"
        mock_get_prompt.return_value = "Template: {file_content} {detail_instruction} {diagram_instruction} {detail_level} {diagram_requested}"

        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "Explanation", []))

        # Run logic
        success = await run_explain_logic(self.args)

        # Assertions
        self.assertTrue(success)
        MockConfig.assert_called_once()
        MockAgent.assert_called_once()
        mock_read_text.assert_called_once()

        # Verify prompt construction
        call_args = mock_agent_instance.run_agent_session.call_args
        self.assertIsNotNone(call_args)
        prompt = call_args[0][0]
        self.assertIn("print('hello world')", prompt)
        self.assertIn("detailed walkthrough", prompt) # Detail=high
        self.assertIn("Do not generate a diagram", prompt) # Diagram=False

    @patch("shared.explain.Config")
    @patch("shared.explain.GeminiAgent")
    @patch("shared.explain.get_explain_prompt")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("pathlib.Path.read_text")
    async def test_run_explain_logic_with_diagram(self, mock_read_text, mock_is_file, mock_exists, mock_get_prompt, MockAgent, MockConfig):
        # Setup mocks
        self.args.diagram = True
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read_text.return_value = "def foo(): pass"
        mock_get_prompt.return_value = "Template: {file_content} {detail_instruction} {diagram_instruction} {detail_level} {diagram_requested}"

        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "Explanation", []))

        # Run logic
        success = await run_explain_logic(self.args)

        # Assertions
        self.assertTrue(success)

        # Verify prompt construction
        call_args = mock_agent_instance.run_agent_session.call_args
        prompt = call_args[0][0]
        self.assertIn("Generate a Mermaid diagram", prompt)

    @patch("shared.explain.Config")
    @patch("shared.explain.GeminiAgent")
    @patch("pathlib.Path.exists")
    async def test_run_explain_logic_file_not_found(self, mock_exists, MockAgent, MockConfig):
        # Setup mocks
        mock_exists.return_value = False

        # Run logic
        success = await run_explain_logic(self.args)

        # Assertions
        self.assertFalse(success)
        MockAgent.assert_not_called()

if __name__ == "__main__":
    unittest.main()
