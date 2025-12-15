import unittest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from pathlib import Path
import json
import asyncio
from shared.config import Config
from agents.gemini.sprint import SprintManager, Task, SprintPlan, run_sprint

class TestSprintManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.project_dir = Path("/tmp/test_project")
        self.config.feature_list_path = self.config.project_dir / "features.json"
        self.config.agent_type = "gemini"
        self.config.max_agents = 2

        self.agent_client = MagicMock()

        self.manager = SprintManager(self.config, self.agent_client)

    @patch("agents.gemini.sprint.GeminiClient")
    @patch("agents.gemini.sprint.run_gemini_session")
    @patch("agents.gemini.sprint.get_sprint_planner_prompt")
    async def test_run_planning_phase_success(self, mock_prompt, mock_run_session, mock_client_cls):
        mock_prompt.return_value = "Plan prompt"

        # Mock successful session response
        plan_json = {
            "sprint_goal": "Goal",
            "tasks": [
                {"id": "1", "title": "Task 1", "dependencies": []},
                {"id": "2", "title": "Task 2", "dependencies": ["1"]}
            ]
        }

        # Mock writing to file via side effect of agent
        # The agent logic in run_planning_phase expects the file to exist after session
        # OR it parses from response.

        mock_run_session.return_value = ("continue", f"```json\n{json.dumps(plan_json)}\n```", [])

        with patch.object(Path, "exists") as mock_exists:
            # First check (app_spec) -> False
            # Second check (feature_list) -> False
            # Third check (sprint_plan.json) -> False (to trigger parsing)
            mock_exists.side_effect = [False, False, False]

            with patch.object(Path, "write_text") as mock_write:
                with patch.object(Path, "read_text") as mock_read:
                    # Mock read_text for validation step
                    mock_read.return_value = json.dumps(plan_json)

                    success = await self.manager.run_planning_phase()

                    self.assertTrue(success)
                    self.assertEqual(len(self.manager.plan.tasks), 2)
                    self.assertEqual(self.manager.tasks_by_id["2"].dependencies, ["1"])

    @patch("agents.gemini.sprint.GeminiClient")
    @patch("agents.gemini.sprint.run_gemini_session")
    @patch("agents.gemini.sprint.get_sprint_worker_prompt")
    @patch("agents.gemini.sprint.AgentClient")
    async def test_run_worker(self, mock_agent_client_cls, mock_prompt, mock_run_session, mock_client_cls):
        task = Task(id="1", title="T1", description="D1")

        mock_worker_client = MagicMock()
        mock_worker_client.poll_commands.return_value.pause_requested = False
        mock_agent_client_cls.return_value = mock_worker_client

        # Mock session to complete task
        mock_run_session.return_value = ("continue", "Done! SPRINT_TASK_COMPLETE", ["action"])

        await self.manager.run_worker(task)

        self.assertEqual(task.status, "COMPLETED")
        self.assertIn("1", self.manager.completed_tasks)
        mock_worker_client.stop.assert_called()

    async def test_execute_sprint_logic(self):
        # Setup plan manually
        t1 = Task(id="1", title="T1", description="D1", status="PENDING")
        t2 = Task(id="2", title="T2", description="D2", status="PENDING", dependencies=["1"])

        self.manager.plan = SprintPlan(sprint_goal="G", tasks=[t1, t2])
        self.manager.tasks_by_id = {"1": t1, "2": t2}

        # Mock run_worker to simulate async completion
        async def mock_worker(task):
            task.status = "IN_PROGRESS"
            await asyncio.sleep(0.1)
            task.status = "COMPLETED"
            self.manager.completed_tasks.add(task.id)
            self.manager.running_tasks.remove(task.id)

        self.manager.run_worker = mock_worker

        await self.manager.execute_sprint()

        self.assertEqual(t1.status, "COMPLETED")
        self.assertEqual(t2.status, "COMPLETED")

if __name__ == "__main__":
    unittest.main()
