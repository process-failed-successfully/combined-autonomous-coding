
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.debug import run_debug_logic

class TestDebugLogic(unittest.IsolatedAsyncioTestCase):

    @patch("shared.debug.subprocess.run")
    async def test_debug_success(self, mock_run):
        # Mock successful execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success"
        mock_run.return_value = mock_result

        success = await run_debug_logic(
            command="echo 'hello'",
            project_dir=Path(".")
        )

        self.assertTrue(success)
        mock_run.assert_called_once()

    @patch("shared.debug.subprocess.run")
    @patch("shared.debug.GeminiAgent")
    @patch("shared.debug.get_file_tree")
    async def test_debug_failure_analysis(self, mock_get_file_tree, mock_agent_class, mock_run):
        # Mock failed execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Error output"
        mock_result.stderr = "Traceback..."
        mock_run.return_value = mock_result

        # Mock File Tree
        mock_get_file_tree.return_value = "file_tree_content"

        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_agent_session.return_value = ("COMPLETED", "Analysis", [])
        mock_agent_class.return_value = mock_agent

        success = await run_debug_logic(
            command="python failing_script.py",
            project_dir=Path("."),
            agent_type="gemini"
        )

        # Should return False because the command failed
        self.assertFalse(success)

        # Verify agent was called
        mock_agent.run_agent_session.assert_called_once()
        args, _ = mock_agent.run_agent_session.call_args
        prompt = args[0]
        self.assertIn("python failing_script.py", prompt)
        self.assertIn("Error output", prompt)
        self.assertIn("Traceback...", prompt)
        self.assertIn("file_tree_content", prompt)

if __name__ == "__main__":
    unittest.main()
