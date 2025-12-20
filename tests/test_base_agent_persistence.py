import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
import shutil
from pathlib import Path
from agents.shared.base_agent import BaseAgent
from shared.config import Config


class ConcreteAgent(BaseAgent):
    def get_agent_type(self) -> str:
        return "test"

    async def run_agent_session(self, prompt, status_callback=None):
        return "continue", "test response", ["action1"]


class TestBaseAgentPersistence(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("tests_output/test_persistence")
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.config = Config(project_dir=self.project_dir, auto_continue_delay=0)
        self.agent = ConcreteAgent(self.config)

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def test_save_and_load_state(self):
        self.agent.iteration = 5
        self.agent.consecutive_errors = 2
        self.agent.is_first_run = False
        self.agent.has_run_manager_first = True
        self.agent.recent_history = ["a", "b"]

        self.agent.save_state()

        state_file = self.agent.get_state_file_path()
        self.assertTrue(state_file.exists())

        content = json.loads(state_file.read_text())
        self.assertEqual(content["iteration"], 5)
        self.assertEqual(content["consecutive_errors"], 2)
        self.assertFalse(content["is_first_run"])
        self.assertTrue(content["has_run_manager_first"])
        self.assertEqual(content["recent_history"], ["a", "b"])

        # Test Load
        new_agent = ConcreteAgent(self.config)
        new_agent.load_state()
        self.assertEqual(new_agent.iteration, 5)
        self.assertEqual(new_agent.consecutive_errors, 2)
        self.assertFalse(new_agent.is_first_run)
        self.assertTrue(new_agent.has_run_manager_first)
        self.assertEqual(new_agent.recent_history, ["a", "b"])

    @patch("agents.shared.base_agent.log_startup_config")
    @patch("agents.shared.base_agent.init_telemetry")
    @patch("agents.shared.base_agent.get_telemetry")
    @patch("agents.shared.base_agent.copy_spec_to_project")
    @patch("agents.shared.base_agent.BaseAgent.run_agent_session", new_callable=AsyncMock)
    def test_loop_saves_state(self, mock_run, mock_copy, mock_get_tel, mock_init_tel, mock_log):
        mock_tel = MagicMock()
        mock_get_tel.return_value = mock_tel
        mock_run.return_value = ("continue", "resp", ["act"])

        self.config.max_iterations = 1

        async def run():
            await self.agent.run_autonomous_loop()

        asyncio.run(run())

        state_file = self.agent.get_state_file_path()
        self.assertTrue(state_file.exists())
        content = json.loads(state_file.read_text())
        self.assertEqual(content["iteration"], 1)

    @patch("agents.shared.base_agent.log_startup_config")
    @patch("agents.shared.base_agent.init_telemetry")
    @patch("agents.shared.base_agent.get_telemetry")
    @patch("agents.shared.base_agent.copy_spec_to_project")
    @patch("agents.shared.base_agent.BaseAgent.run_agent_session", new_callable=AsyncMock)
    def test_loop_resumes_state(self, mock_run, mock_copy, mock_get_tel, mock_init_tel, mock_log):
        mock_tel = MagicMock()
        mock_get_tel.return_value = mock_tel
        mock_run.return_value = ("continue", "resp", ["act"])

        # Pre-create state
        state = {
            "iteration": 10,
            "consecutive_errors": 0,
            "is_first_run": False,
            "has_run_manager_first": False,
            "recent_history": []
        }
        self.agent.get_state_file_path().write_text(json.dumps(state))

        self.config.max_iterations = 11  # Run one more

        async def run():
            await self.agent.run_autonomous_loop()

        asyncio.run(run())

        self.assertEqual(self.agent.iteration, 11)


if __name__ == "__main__":
    unittest.main()
