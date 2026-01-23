import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys
import io

# Import logic to test
from shared.plan import run_plan_logic

class TestPlanLogic(unittest.IsolatedAsyncioTestCase):

    @patch("shared.plan.Config")
    @patch("shared.plan.generate_agent_id")
    @patch("shared.plan.setup_logger")
    @patch("shared.plan.load_config_from_file")
    @patch("shared.plan.ensure_config_exists")
    @patch("agents.gemini.GeminiAgent")
    async def test_run_plan_logic_success(self, MockAgent, MockEnsureConfig, MockLoadConfig, MockSetupLogger, MockGenerateId, MockConfig):
        # Setup mocks
        mock_logger = MagicMock()
        MockSetupLogger.return_value = (mock_logger, None)
        MockGenerateId.return_value = "test-agent-id"
        MockLoadConfig.return_value = {}

        # Mock Config instance
        mock_config_instance = MagicMock()
        mock_config_instance.project_dir = Path("/tmp/test")
        mock_config_instance.spec_file = MagicMock()
        mock_config_instance.spec_file.read_text.return_value = "spec content"
        mock_config_instance.agent_type = "gemini"

        MockConfig.return_value = mock_config_instance

        # Mock Agent instance
        mock_agent_instance = AsyncMock()
        MockAgent.return_value = mock_agent_instance
        mock_agent_instance.run_planning_session.return_value = True

        # Mock filesystem
        with patch("pathlib.Path.exists") as mock_exists, \
             patch("pathlib.Path.read_text") as mock_read_text:

            # Always exist
            mock_exists.return_value = True
            mock_read_text.return_value = '{"features": []}'

            project_dir = Path("/tmp/test")
            spec_file = project_dir / "app_spec.txt"

            success, output = await run_plan_logic(
                project_dir=project_dir,
                spec_file=spec_file,
                agent_type="gemini",
                capture_output=True
            )

            self.assertTrue(success)
            self.assertIn("Plan generated successfully", output)
            self.assertIn('{"features": []}', output)

            mock_agent_instance.run_planning_session.assert_awaited_once()

    @patch("shared.plan.Config")
    @patch("shared.plan.generate_agent_id")
    @patch("shared.plan.setup_logger")
    @patch("shared.plan.load_config_from_file")
    @patch("shared.plan.ensure_config_exists")
    @patch("agents.gemini.GeminiAgent")
    async def test_run_plan_logic_agent_fail(self, MockAgent, MockEnsureConfig, MockLoadConfig, MockSetupLogger, MockGenerateId, MockConfig):
        # Setup mocks
        MockSetupLogger.return_value = (MagicMock(), None)
        MockLoadConfig.return_value = {}

        mock_config_instance = MagicMock()
        mock_config_instance.project_dir = Path("/tmp/test")
        mock_config_instance.spec_file = MagicMock()
        mock_config_instance.spec_file.read_text.return_value = "spec content"
        mock_config_instance.agent_type = "gemini"
        MockConfig.return_value = mock_config_instance

        mock_agent_instance = AsyncMock()
        MockAgent.return_value = mock_agent_instance
        # Agent fails
        mock_agent_instance.run_planning_session.return_value = False

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True # Spec exists

            success, output = await run_plan_logic(
                project_dir=Path("/tmp/test"),
                spec_file=Path("/tmp/test/app_spec.txt"),
                agent_type="gemini",
                capture_output=True
            )

            self.assertFalse(success)
            self.assertIn("Agent failed to generate a plan", output)

if __name__ == '__main__':
    unittest.main()
