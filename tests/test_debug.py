
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.debug import run_debug_logic

class TestDebug(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        # Create a dummy file for file tree context
        (self.project_dir / "test.py").touch()

    @patch("shared.debug.subprocess.run")
    async def test_run_debug_logic_success(self, mock_subprocess):
        # Mock successful command execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_subprocess.return_value = mock_result

        success = await run_debug_logic(
            command="echo 'hello'",
            project_dir=self.project_dir
        )

        self.assertTrue(success)
        mock_subprocess.assert_called_once()
        # Verify the command was run
        args, kwargs = mock_subprocess.call_args
        self.assertEqual(args[0], "echo 'hello'")

    @patch("shared.debug.subprocess.run")
    @patch("shared.debug.GeminiAgent")
    async def test_run_debug_logic_failure(self, mock_agent_class, mock_subprocess):
        # Mock failed command execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error output"
        mock_subprocess.return_value = mock_result

        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("COMPLETED", "AI Analysis Fix", [])
        mock_agent_class.return_value = mock_agent

        success = await run_debug_logic(
            command="fail_command",
            project_dir=self.project_dir,
            agent_type="gemini"
        )

        self.assertTrue(success) # Returns True because analysis was successful

        # Verify subprocess called
        # mock_subprocess.assert_called_once() # Called twice because get_file_tree uses it too
        self.assertGreaterEqual(mock_subprocess.call_count, 1)

        # Verify agent called with prompt containing error info
        mock_agent.run_agent_session.assert_called_once()
        call_args = mock_agent.run_agent_session.call_args
        prompt = call_args[0][0]

        self.assertIn("fail_command", prompt)
        self.assertIn("Error output", prompt)
        self.assertIn("Exit Code: 1", prompt)

    @patch("shared.debug.subprocess.run")
    @patch("shared.debug.GeminiAgent")
    async def test_run_debug_logic_with_files(self, mock_agent_class, mock_subprocess):
        # Create a specific file to include
        (self.project_dir / "relevant.py").write_text("def foo(): pass")

        # Mock failed command
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error"
        mock_subprocess.return_value = mock_result

        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("COMPLETED", "Analysis", [])
        mock_agent_class.return_value = mock_agent

        await run_debug_logic(
            command="cmd",
            project_dir=self.project_dir,
            files=["relevant.py"]
        )

        # Verify prompt contains file content
        call_args = mock_agent.run_agent_session.call_args
        prompt = call_args[0][0]
        self.assertIn("def foo(): pass", prompt)
        self.assertIn("relevant.py", prompt)

if __name__ == "__main__":
    unittest.main()
