from agents.shared.sprint import SprintManager, Task, SprintPlan
from shared.config import Config
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import asyncio
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


class TestSprintManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.project_dir = Path("/tmp/test_project")
        self.config.feature_list_path = self.config.project_dir / "features.json"
        self.config.agent_type = "gemini"
        self.config.max_agents = 2
        self.config.spec_file = self.config.project_dir / "app_spec.txt"

        self.agent_client = MagicMock()

        self.manager = SprintManager(self.config, self.agent_client)

    @patch("agents.shared.sprint.GeminiClient")
    @patch("agents.shared.sprint.run_gemini_session")
    @patch("agents.shared.sprint.get_sprint_planner_prompt")
    async def test_run_planning_phase_success(
        self, mock_prompt, mock_run_session, mock_client_cls
    ):
        mock_prompt.return_value = "Plan prompt"

        # Mock successful session response
        plan_json = {
            "sprint_goal": "Goal",
            "tasks": [
                {"id": "1", "title": "Task 1", "dependencies": []},
                {"id": "2", "title": "Task 2", "dependencies": ["1"]},
            ],
        }

        mock_run_session.return_value = (
            "continue",
            f"```json\n{json.dumps(plan_json)}\n```",
            [],
        )

        with patch.object(Path, "exists") as mock_exists:
            # First check (app_spec) -> False
            # Second check (feature_list) -> False
            # Third check (sprint_plan.json) -> False (to trigger parsing)
            mock_exists.side_effect = [False, False, False]

            with patch.object(Path, "write_text"):
                with patch.object(Path, "read_text") as mock_read:
                    # Mock read_text for validation step
                    mock_read.return_value = json.dumps(plan_json)

                    success = await self.manager.run_planning_phase()

                    self.assertTrue(success)
                    self.assertEqual(len(self.manager.plan.tasks), 2)
                    self.assertEqual(self.manager.tasks_by_id["2"].dependencies, ["1"])

    @patch("agents.shared.sprint.GeminiClient")
    @patch("agents.shared.sprint.run_gemini_session")
    @patch("agents.shared.sprint.get_sprint_planner_prompt")
    async def test_run_planning_phase_parsing_fail(
        self, mock_prompt, mock_run_session, mock_client_cls
    ):
        mock_prompt.return_value = "Plan prompt"
        # Mock response without valid JSON
        mock_run_session.return_value = ("continue", "Invalid response", [])

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [False, False, False]
            success = await self.manager.run_planning_phase()
            self.assertFalse(success)

    @patch("agents.shared.sprint.GeminiClient")
    @patch("agents.shared.sprint.run_gemini_session")
    @patch("agents.shared.sprint.get_sprint_worker_prompt")
    @patch("agents.shared.sprint.AgentClient")
    async def test_run_worker_success(
        self, mock_agent_client_cls, mock_prompt, mock_run_session, mock_client_cls
    ):
        task = Task(id="1", title="T1", description="D1")

        mock_worker_client = MagicMock()
        mock_worker_client.poll_commands.return_value.pause_requested = False
        mock_agent_client_cls.return_value = mock_worker_client

        mock_run_session.return_value = (
            "continue",
            "Done! SPRINT_TASK_COMPLETE",
            ["action"],
        )

        await self.manager.run_worker(task)

        self.assertEqual(task.status, "COMPLETED")
        self.assertIn("1", self.manager.completed_tasks)
        mock_worker_client.stop.assert_called()

    @patch("agents.shared.sprint.GeminiClient")
    @patch("agents.shared.sprint.run_gemini_session")
    @patch("agents.shared.sprint.get_sprint_worker_prompt")
    @patch("agents.shared.sprint.AgentClient")
    async def test_run_worker_failed_response(
        self, mock_agent_client_cls, mock_prompt, mock_run_session, mock_client_cls
    ):
        task = Task(id="1", title="T1", description="D1")

        mock_worker_client = MagicMock()
        mock_worker_client.poll_commands.return_value.pause_requested = False
        mock_agent_client_cls.return_value = mock_worker_client

        mock_run_session.return_value = (
            "continue",
            "Failed! SPRINT_TASK_FAILED",
            ["action"],
        )

        await self.manager.run_worker(task)

        self.assertEqual(task.status, "FAILED")
        self.assertIn("1", self.manager.failed_tasks)
        mock_worker_client.stop.assert_called()

    @patch("agents.shared.sprint.GeminiClient")
    @patch("agents.shared.sprint.run_gemini_session")
    @patch("agents.shared.sprint.get_sprint_worker_prompt")
    @patch("agents.shared.sprint.AgentClient")
    async def test_run_worker_crash(
        self, mock_agent_client_cls, mock_prompt, mock_run_session, mock_client_cls
    ):
        task = Task(id="1", title="T1", description="D1")

        mock_worker_client = MagicMock()
        mock_worker_client.poll_commands.return_value.pause_requested = False
        mock_agent_client_cls.return_value = mock_worker_client

        mock_run_session.side_effect = Exception("Crash")

        await self.manager.run_worker(task)

        mock_worker_client.stop.assert_called()

    async def test_execute_sprint_logic(self):
        # Setup plan manually
        t1 = Task(id="1", title="T1", description="D1", status="PENDING")
        t2 = Task(
            id="2", title="T2", description="D2", status="PENDING", dependencies=["1"]
        )

        self.manager.plan = SprintPlan(sprint_goal="G", tasks=[t1, t2])
        self.manager.tasks_by_id = {"1": t1, "2": t2}

        # Mock run_worker to simulate async completion
        async def mock_worker(task):
            task.status = "IN_PROGRESS"
            await asyncio.sleep(0.01)
            task.status = "COMPLETED"
            self.manager.completed_tasks.add(task.id)
            self.manager.running_tasks.remove(task.id)

        self.manager.run_worker = mock_worker

        await self.manager.execute_sprint()

        self.assertEqual(t1.status, "COMPLETED")
        self.assertEqual(t2.status, "COMPLETED")

    def test_update_feature_list_success(self):
        features = [{"name": "F1", "status": "pending"}]
        self.manager.plan = SprintPlan(
            sprint_goal="G",
            tasks=[Task(id="1", title="T1", description="D1", status="COMPLETED", feature_name="F1")]
        )

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            with patch.object(Path, "read_text") as mock_read:
                mock_read.return_value = json.dumps(features)
                with patch.object(Path, "write_text") as mock_write:

                    self.manager.update_feature_list()

                    # Verify write was called with updated status
                    args, _ = mock_write.call_args
                    written_data = json.loads(args[0])
                    self.assertEqual(written_data[0]["status"], "completed")

    def test_update_feature_list_missing_file(self):
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            # Should just return without error
            self.manager.update_feature_list()


if __name__ == "__main__":
    unittest.main()
