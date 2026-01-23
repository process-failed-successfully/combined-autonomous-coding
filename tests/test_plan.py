import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import os
import io

from shared.plan import run_plan_logic
from shared.config import Config

class TestPlanLogic(unittest.IsolatedAsyncioTestCase):

    @patch("shared.plan.load_config_from_file")
    @patch("shared.plan.ensure_config_exists")
    @patch("shared.plan.generate_agent_id")
    @patch("shared.plan.GeminiAgent")
    async def test_run_plan_logic_success(self, mock_gemini_agent, mock_generate_id, mock_ensure_config, mock_load_config):
        # Setup Mocks
        mock_load_config.return_value = {}
        mock_generate_id.return_value = "test-agent-id"

        mock_agent_instance = MagicMock()
        mock_gemini_agent.return_value = mock_agent_instance
        mock_agent_instance.run_planning_session = AsyncMock(return_value=True)

        project_dir = Path("./test_project")
        project_dir.mkdir(exist_ok=True)
        spec_file = project_dir / "app_spec.txt"
        spec_file.write_text("Test Spec")

        feature_file = project_dir / "feature_list.json"
        feature_file.write_text('{"features": []}')

        try:
            success, message = await run_plan_logic(
                project_dir=project_dir,
                agent_type="gemini",
                model="test-model",
                spec_file=spec_file,
                capture_output=True
            )

            self.assertTrue(success)
            self.assertIn("Plan generated successfully", message)
            mock_agent_instance.run_planning_session.assert_called_once()

        finally:
            if spec_file.exists():
                spec_file.unlink()
            if feature_file.exists():
                feature_file.unlink()
            if project_dir.exists():
                project_dir.rmdir()

    @patch("shared.plan.load_config_from_file")
    @patch("shared.plan.ensure_config_exists")
    @patch("shared.plan.generate_agent_id")
    @patch("shared.plan.GeminiAgent")
    async def test_run_plan_logic_failure(self, mock_gemini_agent, mock_generate_id, mock_ensure_config, mock_load_config):
        # Setup Mocks
        mock_load_config.return_value = {}
        mock_generate_id.return_value = "test-agent-id"

        mock_agent_instance = MagicMock()
        mock_gemini_agent.return_value = mock_agent_instance
        mock_agent_instance.run_planning_session = AsyncMock(return_value=False)

        project_dir = Path("./test_project_fail")
        project_dir.mkdir(exist_ok=True)
        spec_file = project_dir / "app_spec.txt"
        spec_file.write_text("Test Spec")

        try:
            success, message = await run_plan_logic(
                project_dir=project_dir,
                agent_type="gemini",
                model="test-model",
                spec_file=spec_file,
                capture_output=True
            )

            self.assertFalse(success)
            self.assertIn("Agent failed to generate a plan", message)

        finally:
            if spec_file.exists():
                spec_file.unlink()
            if project_dir.exists():
                project_dir.rmdir()

    async def test_run_plan_logic_missing_spec(self):
        success, message = await run_plan_logic(
            project_dir=Path("."),
            agent_type="gemini",
            model="test-model",
            spec_file=None,
            capture_output=True
        )
        self.assertFalse(success)
        self.assertIn("A valid spec file is required", message)

if __name__ == "__main__":
    unittest.main()
