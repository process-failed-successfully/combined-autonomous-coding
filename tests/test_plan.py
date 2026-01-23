import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.plan import run_plan_logic

class TestPlanLogic(unittest.IsolatedAsyncioTestCase):
    @patch("shared.plan.GeminiAgent")
    @patch("shared.plan.load_config_from_file")
    @patch("shared.plan.ensure_config_exists")
    async def test_run_plan_success(self, mock_ensure, mock_load, mock_agent_class):
        mock_load.return_value = {}

        mock_agent = AsyncMock()
        mock_agent.run_planning_session.return_value = True
        mock_agent_class.return_value = mock_agent

        # We need to mock Path object interactions carefully
        with patch("pathlib.Path.exists") as mock_exists, \
             patch("pathlib.Path.read_text") as mock_read:

            # 1. Spec file exists check -> True
            # 2. Feature list file exists check (after generation) -> True
            mock_exists.side_effect = [True, True]

            # 1. Read spec content
            # 2. Read feature list content
            mock_read.side_effect = ["Spec content", '{"features": []}']

            success, message = await run_plan_logic(Path("."), "spec.txt", capture_output=True)

            self.assertTrue(success)
            self.assertIn('"features": []', message)
            mock_agent.run_planning_session.assert_called_once()

    @patch("shared.plan.GeminiAgent")
    @patch("shared.plan.load_config_from_file")
    @patch("shared.plan.ensure_config_exists")
    async def test_run_plan_failure(self, mock_ensure, mock_load, mock_agent_class):
        mock_load.return_value = {}

        mock_agent = AsyncMock()
        mock_agent.run_planning_session.return_value = False
        mock_agent_class.return_value = mock_agent

        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value="Spec"):

            success, message = await run_plan_logic(Path("."), "spec.txt", capture_output=True)

            self.assertFalse(success)
            self.assertIn("Agent failed", message)

if __name__ == "__main__":
    unittest.main()
