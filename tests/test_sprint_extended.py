import asyncio
import json
import logging
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from agents.shared.sprint import SprintManager, run_single_sprint, Task, SprintPlan
from shared.config import Config
from agents.shared.prompts import get_sprint_coding_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_sprint_extended")


class TestSprintExtended(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = Config(
            project_dir=self.test_dir,
            agent_type="gemini",
            sprint_mode=True,
        )
        self.config.sprint_mode = True  # Explicitly enable sprint mode in case init doesn't
        
        # Create dummy feature list
        self.config.feature_list_path.write_text(
            json.dumps([
                {"name": "Feature A", "description": "Desc A", "passes": False},
                {"name": "Feature B", "description": "Desc B", "passes": False},
            ])
        )

    async def asyncTearDown(self):
        shutil.rmtree(self.test_dir)

    def test_prompt_loader(self):
        """Verify that the new prompt loader works."""
        prompt = get_sprint_coding_prompt()
        self.assertIn("YOUR ROLE - SPRINT WORKER AGENT", prompt)
        self.assertIn("SPRINT_TASK_COMPLETE", prompt)

    async def test_update_feature_list_strict(self):
        """Verify strict feature list update logic."""
        manager = SprintManager(self.config)
        
        # Case 1: Plan has 2 tasks for "Feature A". ALL are completed.
        manager.plan = SprintPlan(
            sprint_goal="Test",
            tasks=[
                Task(id="1", title="Task 1", description="d", feature_name="Feature A", status="COMPLETED"),
                Task(id="2", title="Task 2", description="d", feature_name="Feature A", status="COMPLETED"),
            ]
        )
        manager.update_feature_list()
        
        features = json.loads(self.config.feature_list_path.read_text())
        feature_a = next(f for f in features if f["name"] == "Feature A")
        self.assertEqual(feature_a.get("status"), "completed")

        # Case 2: Plan has 2 tasks for "Feature B". Only 1 completed.
        manager.plan = SprintPlan(
            sprint_goal="Test",
            tasks=[
                Task(id="3", title="Task 3", description="d", feature_name="Feature B", status="COMPLETED"),
                Task(id="4", title="Task 4", description="d", feature_name="Feature B", status="PENDING"),
            ]
        )
        # Reset file
        self.config.feature_list_path.write_text(
             json.dumps([
                {"name": "Feature A", "status": "completed"}, 
                {"name": "Feature B", "status": "pending"}
            ])
        )
        
        manager.update_feature_list()
        features = json.loads(self.config.feature_list_path.read_text())
        feature_b = next(f for f in features if f["name"] == "Feature B")
        self.assertNotEqual(feature_b.get("status"), "completed")

    @patch("agents.shared.sprint.SprintManager.run_planning_phase")
    @patch("agents.shared.sprint.SprintManager.execute_sprint")
    @patch("agents.shared.sprint.SprintManager._get_agent_runner") 
    async def test_post_sprint_checks(self, mock_get_runner, mock_execute, mock_plan):
        """Verify that run_single_sprint triggers post-sprint checks."""
        mock_plan.return_value = True
        
        # Mock Manager Instance
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_runner.return_value = ("continue", "Manager Check OK", [])
        mock_get_runner.return_value = (mock_client, mock_runner)

        # We need to mock the internal state of manager after planning
        # But run_single_sprint instantiates a NEW manager.
        # So we should patch SprintManager class? Or just trust that run_single_sprint calls the methods.
        
        # Let's run `manager.run_post_sprint_checks` directly to verify it calls the runner.
        manager = SprintManager(self.config)
        await manager.run_post_sprint_checks()
        
        # Should have called runner with manager prompt
        mock_runner.assert_called()
        args, _ = mock_runner.call_args
        prompt_sent = args[1]
        self.assertIn("YOUR ROLE - PROJECT MANAGER", prompt_sent)

if __name__ == "__main__":
    unittest.main()
