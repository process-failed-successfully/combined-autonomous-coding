import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
import asyncio
from shared.plan import run_plan_logic

class TestPlanLogic(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.spec_file = self.project_dir / "app_spec.txt"
        self.spec_file.write_text("Test Spec")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.plan.GeminiAgent")
    async def test_run_plan_logic_success(self, mock_agent_class):
        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_planning_session.return_value = True
        mock_agent_class.return_value = mock_agent

        # Create dummy feature_list.json as if agent created it
        feature_file = self.project_dir / "feature_list.json"
        feature_file.write_text('[]')

        # Run logic
        success, msg = await run_plan_logic(
            project_dir=self.project_dir,
            spec_file=self.spec_file,
            agent_type="gemini",
            verbose=False
        )

        self.assertTrue(success)
        self.assertEqual(msg, "[]")
        mock_agent.run_planning_session.assert_called_once()

    @patch("shared.plan.GeminiAgent")
    async def test_run_plan_logic_failure_no_plan(self, mock_agent_class):
        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.run_planning_session.return_value = True
        mock_agent_class.return_value = mock_agent

        # Do NOT create feature_list.json (simulating agent failure to write file)

        # Run logic
        success, msg = await run_plan_logic(
            project_dir=self.project_dir,
            spec_file=self.spec_file,
            agent_type="gemini",
            verbose=False
        )

        self.assertFalse(success)
        self.assertIn("did not produce a plan", msg)

    async def test_run_plan_logic_no_spec(self):
        # Spec does not exist
        non_existent_spec = self.project_dir / "non_existent.txt"

        success, msg = await run_plan_logic(
            project_dir=self.project_dir,
            spec_file=non_existent_spec,
            agent_type="gemini",
            verbose=False
        )

        self.assertFalse(success)
        self.assertIn("Spec file not found", msg)

if __name__ == "__main__":
    unittest.main()
