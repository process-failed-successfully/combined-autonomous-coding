"""
Tests for the CLI command generation feature ('do' command).
"""

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import sys
import io

# Ensure the shared module can be imported
sys.path.append(str(Path(__file__).parent.parent))

from shared.cli import run_do_logic

class TestCliFeature(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.instruction = "list all python files"

    @patch("shared.cli.GeminiAgent")
    @patch("builtins.input", return_value="n") # Default to no
    async def test_run_do_logic_basic(self, mock_input, MockAgent):
        """Test basic flow where agent returns a command."""
        mock_agent_instance = MockAgent.return_value
        # Mock run_agent_session to return a command
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "find . -name '*.py'", []))

        # Capture stdout
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            success = await run_do_logic(
                instruction=self.instruction,
                project_dir=self.project_dir,
                agent_type="gemini"
            )

            output = fake_out.getvalue()
            self.assertIn("find . -name '*.py'", output)
            self.assertTrue(success) # Should return True because we gracefully aborted

    @patch("shared.cli.GeminiAgent")
    @patch("subprocess.run")
    async def test_run_do_logic_execute_yes(self, mock_subprocess, MockAgent):
        """Test execution when user says yes (simulated by yes=True arg)."""
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "echo 'hello'", []))

        mock_subprocess.return_value.returncode = 0

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            success = await run_do_logic(
                instruction="say hello",
                project_dir=self.project_dir,
                agent_type="gemini",
                yes=True
            )

            output = fake_out.getvalue()
            self.assertIn("Running: echo 'hello'", output)
            self.assertTrue(success)
            mock_subprocess.assert_called_with("echo 'hello'", shell=True, cwd=unittest.mock.ANY)

    @patch("shared.cli.GeminiAgent")
    async def test_run_do_logic_error_response(self, MockAgent):
        """Test handling of error response from agent."""
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "ERROR: Ambiguous instruction", []))

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            success = await run_do_logic(
                instruction="do something undefined",
                project_dir=self.project_dir,
                agent_type="gemini"
            )

            output = fake_out.getvalue()
            self.assertIn("Agent Error: Ambiguous instruction", output)
            self.assertFalse(success)

    @patch("shared.cli.GeminiAgent")
    @patch("builtins.input", return_value="y")
    @patch("subprocess.run")
    async def test_run_do_logic_interactive_yes(self, mock_subprocess, mock_input, MockAgent):
        """Test interactive confirmation."""
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "ls -la", []))

        mock_subprocess.return_value.returncode = 0

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            success = await run_do_logic(
                instruction="list files",
                project_dir=self.project_dir,
                agent_type="gemini"
            )

            output = fake_out.getvalue()
            self.assertIn("Run this command? [y/N]:", str(mock_input.call_args)) # Can't check stdout for input prompt easily
            self.assertIn("Running: ls -la", output)
            self.assertTrue(success)

    @patch("shared.cli.GeminiAgent")
    async def test_run_do_logic_markdown_stripping(self, MockAgent):
        """Test that markdown code blocks are stripped."""
        mock_agent_instance = MockAgent.return_value
        # Agent returns markdown block
        response = "```bash\necho 'hello'\n```"
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, response, []))

        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            # We pass yes=True to skip input
            await run_do_logic(
                instruction="say hello",
                project_dir=self.project_dir,
                agent_type="gemini",
                yes=True
            )

            output = fake_out.getvalue()
            # Should not contain backticks
            self.assertIn("echo 'hello'", output)
            self.assertNotIn("```", output)

if __name__ == "__main__":
    unittest.main()
