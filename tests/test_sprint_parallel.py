import asyncio
import json
import logging
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.gemini.sprint import SprintManager
from shared.config import Config

# Configure logging to show timing
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_sprint")


class TestSprintParallel(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = Config(
            project_dir=self.test_dir,
            agent_type="gemini",
            max_agents=5,  # Allow multiple agents
        )
        # Create dummy feature list
        self.config.feature_list_path.write_text(
            json.dumps(
                [
                    {"name": "Feature A", "description": "Independent feature A"},
                    {"name": "Feature B", "description": "Independent feature B"},
                ]
            )
        )

    async def asyncTearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("agents.gemini.sprint.run_gemini_session")
    async def test_parallel_execution(self, mock_run_gemini):
        """
        Verify that independent tasks are executed in parallel.
        We mock the Planner to return a plan with 2 independent tasks.
        We mock the Worker to take 1 second each.
        If parallel, total time should be ~1s, not ~2s.
        """

        # 1. Mock Planner Response
        plan_json = json.dumps(
            {
                "sprint_goal": "Parallel Test",
                "tasks": [
                    {
                        "id": "task_a",
                        "title": "Task A",
                        "description": "Do A",
                        "dependencies": [],
                    },
                    {
                        "id": "task_b",
                        "title": "Task B",
                        "description": "Do B",
                        "dependencies": [],
                    },
                ],
            }
        )

        # First call is Planning, return success and the JSON
        # Subsequent calls are Workers. We need to handle them differently or mock run_worker directly.
        # Ideally we mock _get_agent_runner to return different mocks for
        # planner vs worker.

        # Let's mock SprintManager.run_worker instead for precise control over
        # timing

        manager = SprintManager(self.config)

        # Bypass the planning phase LLM call by injecting the plan directly
        # (Or we can mock run_planning_phase, but we want to test that parsing works too)

        # Setup mock for planning phase
        mock_run_gemini.return_value = ("success", f"```json\n{plan_json}\n```", [])

        # Override run_worker with a slow fake worker
        active_workers = 0
        max_concurrent_workers = 0

        async def fake_worker(task):
            nonlocal active_workers, max_concurrent_workers
            active_workers += 1
            max_concurrent_workers = max(max_concurrent_workers, active_workers)
            logger.info(f"Worker {task.id} started. Active: {active_workers}")
            await asyncio.sleep(0.1)  # Simulate work
            task.status = "COMPLETED"
            manager.completed_tasks.add(task.id)
            manager.running_tasks.remove(task.id)
            active_workers -= 1
            logger.info(f"Worker {task.id} finished. Active: {active_workers}")

        manager.run_worker = fake_worker

        # Run!
        start_time = asyncio.get_running_loop().time()

        # We need to run planning first
        await manager.run_planning_phase()

        # Then execute
        await manager.execute_sprint()

        end_time = asyncio.get_running_loop().time()
        duration = end_time - start_time

        logger.info(f"Total Duration: {duration:.2f}s")
        logger.info(f"Max Concurrent Workers: {max_concurrent_workers}")

        # Assertions
        self.assertEqual(len(manager.completed_tasks), 2)
        self.assertGreaterEqual(
            max_concurrent_workers, 2, "Should have had at least 2 concurrent workers"
        )
        # Polling loop is 1s, so duration will be at least 1s.
        # But if sequential, it would be 0.1 + 0.1 + overhead? No, sequential + poll = long.
        # Parallel test is satisfied by max_concurrent_workers check.


if __name__ == "__main__":
    unittest.main()
