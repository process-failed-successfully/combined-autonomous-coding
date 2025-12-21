"""
Tests for BaseAgent
===================
"""

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from pathlib import Path
from agents.shared.base_agent import BaseAgent
from shared.config import Config


class ConcreteAgent(BaseAgent):
    def get_agent_type(self) -> str:
        return "test"

    async def run_agent_session(self, prompt, status_callback=None):
        # Return status 'done' to stop the loop or 'continue' but we need to mock other things
        return "done", "test response", ["action1"]


class TestBaseAgent(unittest.TestCase):
    def setUp(self):
        # Use a temporary directory for project_dir
        self.project_dir = Path("/tmp/test_project_base_agent")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.config = Config(project_dir=self.project_dir, auto_continue_delay=0)
        self.agent = ConcreteAgent(self.config)

    def tearDown(self):
        # Clean up
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def test_init(self):
        self.assertEqual(self.agent.get_agent_type(), "test")
        self.assertEqual(self.agent.iteration, 0)
        self.assertFalse(self.agent.has_run_manager_first)

    @patch("agents.shared.prompts.get_coding_prompt")
    def test_select_prompt_coding(self, mock_coding):
        mock_coding.return_value = "coding prompt"
        self.agent.iteration = 1
        self.agent.is_first_run = False
        prompt, using_manager = self.agent.select_prompt()
        self.assertEqual(prompt, "coding prompt")
        self.assertFalse(using_manager)

    @patch("agents.shared.prompts.get_initializer_prompt")
    def test_select_prompt_initializer(self, mock_init):
        mock_init.return_value = "init prompt"
        self.agent.is_first_run = True
        prompt, using_manager = self.agent.select_prompt()
        self.assertEqual(prompt, "init prompt")
        self.assertFalse(using_manager)

    def test_inject_jira_context(self):
        self.config.jira = MagicMock()
        self.config.jira_ticket_key = "PROJ-123"
        self.config.agent_id = "agent-abc-12345678"
        prompt = "Working on {jira_ticket_context} in {unique_branch_suffix}"
        injected = self.agent.inject_jira_context(prompt)
        self.assertIn("PROJ-123", injected)
        self.assertIn("12345678", injected)

    @patch("agents.shared.base_agent.log_startup_config")
    @patch("agents.shared.base_agent.init_telemetry")
    @patch("agents.shared.base_agent.get_telemetry")
    @patch("agents.shared.base_agent.copy_spec_to_project")
    def test_run_autonomous_loop_max_iterations(self, mock_copy, mock_get_tel, mock_init_tel, mock_log):
        # Mock telemetry to avoid errors
        mock_tel = MagicMock()
        mock_get_tel.return_value = mock_tel

        self.config.max_iterations = 0

        # We need to run this in an event loop
        async def run_test():
            await self.agent.run_autonomous_loop()

        asyncio.run(run_test())
        self.assertEqual(self.agent.iteration, 0)

    @patch("agents.shared.base_agent.log_startup_config")
    @patch("agents.shared.base_agent.init_telemetry")
    @patch("agents.shared.base_agent.get_telemetry")
    @patch("agents.shared.base_agent.copy_spec_to_project")
    @patch("agents.shared.base_agent.BaseAgent.run_agent_session", new_callable=AsyncMock)
    def test_run_autonomous_loop_one_iteration(self, mock_run_session, mock_copy, mock_get_tel, mock_init_tel, mock_log):
        # Mock telemetry
        mock_tel = MagicMock()
        mock_get_tel.return_value = mock_tel

        # Setup one iteration
        self.config.max_iterations = 1
        self.agent.is_first_run = False

        # Mock run_agent_session to return 'done'
        mock_run_session.return_value = ("done", "response", ["action"])

        async def run_test():
            await self.agent.run_autonomous_loop()

        asyncio.run(run_test())
        self.assertEqual(self.agent.iteration, 1)


if __name__ == "__main__":
    unittest.main()
