import unittest
from unittest.mock import patch, MagicMock, AsyncMock, ANY, call
from pathlib import Path
import json
import asyncio
from shared.config import Config
from agents.cursor.agent import run_agent_session, run_autonomous_agent

class TestCursorAgent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.config = MagicMock(spec=Config)
        self.config.project_dir = Path("/tmp/test_project")
        self.config.feature_list_path = self.config.project_dir / "features.json"
        self.config.progress_file_path = self.config.project_dir / "progress.txt"
        self.config.model = "test-model"
        self.config.max_iterations = 10
        self.config.manager_frequency = 5
        self.config.run_manager_first = False
        self.config.auto_continue_delay = 0.1
        self.config.max_consecutive_errors = 3
        self.config.login_mode = False
        self.config.verify_creation = False

        self.client = MagicMock()
        self.client.config = self.config
        self.client.run_command = AsyncMock()

        # Default mock for run_command
        self.client.run_command.return_value = {"content": "response"}

    @patch("agents.cursor.agent.get_file_tree")
    @patch("agents.cursor.agent.process_response_blocks")
    @patch("agents.cursor.agent.get_telemetry")
    async def test_run_agent_session_basic(self, mock_telemetry, mock_process_blocks, mock_get_tree):
        mock_get_tree.return_value = "file tree"
        mock_process_blocks.return_value = ("log", ["action1"])

        status, response, actions = await run_agent_session(
            self.client, "prompt", ["history"], None
        )

        self.assertEqual(status, "continue")
        self.assertEqual(response, "response")
        self.assertEqual(actions, ["action1"])

        self.client.run_command.assert_called()
        mock_telemetry.return_value.record_histogram.assert_called()

    @patch("agents.cursor.agent.get_file_tree")
    @patch("agents.cursor.agent.process_response_blocks")
    async def test_run_agent_session_error(self, mock_process_blocks, mock_get_tree):
        mock_get_tree.return_value = "file tree"
        self.client.run_command.side_effect = Exception("Run failed")

        status, response, actions = await run_agent_session(
            self.client, "prompt", [], None
        )

        self.assertEqual(status, "error")
        self.assertIn("Run failed", response)
        self.assertEqual(actions, [])

    @patch("agents.cursor.agent.get_file_tree")
    async def test_run_agent_session_candidates_format(self, mock_get_tree):
        # Mock Cursor response with "candidates" format
        self.client.run_command.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "candidate text"}]}}
            ]
        }

        with patch("agents.cursor.agent.process_response_blocks", return_value=("", [])):
            status, response, actions = await run_agent_session(
                self.client, "prompt", [], None
            )
            self.assertEqual(response, "candidate text")

    @patch("agents.cursor.agent.log_startup_config")
    @patch("agents.cursor.agent.init_telemetry")
    @patch("agents.cursor.agent.get_telemetry")
    @patch("agents.cursor.agent.CursorClient")
    @patch("agents.cursor.agent.run_agent_session")
    @patch("agents.cursor.agent.get_initializer_prompt")
    @patch("agents.cursor.agent.copy_spec_to_project")
    async def test_run_autonomous_agent_first_run(
        self, mock_copy_spec, mock_get_init_prompt, mock_run_session,
        mock_client_cls, mock_get_telemetry, mock_init_telemetry, mock_log_config
    ):
        # Setup mocks
        mock_client_cls.return_value = self.client

        # Simulate is_first_run = True (feature file not exist)
        with patch.object(Path, "exists", return_value=False):
            # run_agent_session returns "continue", "resp", []
            mock_run_session.return_value = ("continue", "resp", [])

            # Use Config with max_iterations=1 to exit loop
            self.config.max_iterations = 1

            await run_autonomous_agent(self.config, None)

            mock_copy_spec.assert_called()
            mock_get_init_prompt.assert_called()
            mock_run_session.assert_called()
            mock_init_telemetry.assert_called()

    @patch("agents.cursor.agent.log_startup_config")
    @patch("agents.cursor.agent.init_telemetry")
    @patch("agents.cursor.agent.get_telemetry")
    @patch("agents.cursor.agent.CursorClient")
    @patch("agents.cursor.agent.run_agent_session")
    @patch("agents.cursor.agent.get_coding_prompt")
    @patch("agents.cursor.agent.log_progress_summary")
    async def test_run_autonomous_agent_coding_run(
        self, mock_log_progress, mock_get_coding_prompt, mock_run_session,
        mock_client_cls, mock_get_telemetry, mock_init_telemetry, mock_log_config
    ):
        mock_client_cls.return_value = self.client

        # Simulate is_first_run = False
        with patch.object(Path, "exists") as mock_exists:
            # We need carefully mock exists calls
            # 1. mkdir parents (True/False doesn't matter much)
            # 2. config.feature_list_path.exists() -> True (First run check)
            # 3. PROJECT_SIGNED_OFF exists -> False
            # 4. human_in_loop exists -> False
            # 5. TRIGGER_MANAGER exists -> False

            # It's tricky with side_effect because Path.exists is called many times.
            # Let's assume most exist checks return False except feature_list_path which we want True.

            def side_effect_exists():
                # We can't really access 'self' (the Path object) easily in side_effect without wrapper
                return False

            # Simpler: use MagicMock for paths in Config?
            # self.config.feature_list_path is a Path.
            # Let's mock the Path objects in config directly.
            pass

        self.config.feature_list_path = MagicMock()
        self.config.feature_list_path.exists.return_value = True

        # PROJECT_SIGNED_OFF
        self.config.project_dir = MagicMock()
        self.config.project_dir.__truediv__.return_value.exists.return_value = False

        # run_agent_session
        mock_run_session.return_value = ("continue", "resp", [])

        self.config.max_iterations = 1

        await run_autonomous_agent(self.config, None)

        mock_log_progress.assert_called()
        mock_get_coding_prompt.assert_called()

    @patch("agents.cursor.agent.log_startup_config")
    @patch("agents.cursor.agent.init_telemetry")
    @patch("agents.cursor.agent.get_telemetry")
    @patch("agents.cursor.agent.CursorClient")
    @patch("agents.cursor.agent.run_agent_session")
    async def test_run_autonomous_agent_human_loop(
        self, mock_run_session,
        mock_client_cls, mock_get_telemetry, mock_init_telemetry, mock_log_config
    ):
        mock_client_cls.return_value = self.client
        self.config.feature_list_path = MagicMock()
        self.config.feature_list_path.exists.return_value = True

        self.config.project_dir = MagicMock()
        # Mock human_in_loop.txt existing
        human_loop_file = MagicMock()
        human_loop_file.exists.return_value = True
        human_loop_file.read_text.return_value = "Need help"

        # Configure project_dir / "human_in_loop.txt" to return this mock
        def get_file(name):
            if name == "human_in_loop.txt":
                return human_loop_file
            if name == "PROJECT_SIGNED_OFF":
                m = MagicMock()
                m.exists.return_value = False
                return m
            return MagicMock()

        self.config.project_dir.__truediv__.side_effect = get_file

        self.config.max_iterations = 5

        await run_autonomous_agent(self.config, None)

        # Should break loop early
        mock_run_session.assert_not_called()

if __name__ == "__main__":
    unittest.main()
