import unittest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open as unittest_mock_open
import tempfile
import asyncio
from pathlib import Path
import os
import sys

# Ensure the root of the project is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_replay

class TestReplayCommand(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory to act as the project root
        self.temp_project_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_project_dir.name)
        # Use a consistent posix path for the log file content
        self.project_dir_str = self.project_dir.as_posix()

    def tearDown(self):
        # Cleanup the temporary directory
        self.temp_project_dir.cleanup()

    @patch('main.run_gemini', new_callable=AsyncMock)
    @patch('main.setup_logger')
    def test_replay_gemini_agent_successful(self, mock_setup_logger, mock_run_gemini):
        # --- Arrange ---
        mock_logger = MagicMock()
        mock_setup_logger.return_value = (mock_logger, None)

        run_id = "test_run_12345"
        # Create realistic log content with a config line
        log_content = f"""
2023-10-27 10:00:00,123 - INFO - Starting Gemini Agent on .
2023-10-27 10:00:00,123 - INFO - Generated Agent ID: {run_id}
2023-10-27 10:00:00,123 - INFO - config: {{'project_dir': PosixPath('{self.project_dir_str}'), 'agent_id': '{run_id}', 'agent_type': 'gemini', 'model': 'gemini-1.5-pro-test', 'max_iterations': 15, 'verbose': False, 'stream_output': True, 'spec_file': PosixPath('{self.project_dir_str}/app_spec.txt'), 'verify_creation': False, 'manager_frequency': 10, 'manager_model': None, 'run_manager_first': False, 'login_mode': False, 'timeout': 600.0, 'max_error_wait': 600.0, 'sprint_mode': False, 'max_agents': 1, 'slack_webhook_url': None, 'discord_webhook_url': None, 'notification_settings': None, 'dind_enabled': False, 'jira': None, 'jira_ticket_key': None, 'jira_spec_content': None, 'feature_list_path': PosixPath('{self.project_dir_str}/feature_list.json')}}
2023-10-27 10:00:01,000 - INFO - Iteration 1/15
"""

        # Mock the command-line arguments passed to run_replay
        mock_args = MagicMock()
        mock_args.run_id = run_id
        mock_args.verbose = True # We can override verbose flag

        # --- Act & Assert ---
        # Mock the file system interactions:
        # 1. `pathlib.Path.exists` should return True for the log file.
        # 2. `builtins.open` should return our mock log content.
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', unittest_mock_open(read_data=log_content)):

            # The function calls sys.exit(), so we catch it
            with self.assertRaises(SystemExit) as cm:
                asyncio.run(run_replay(mock_args))

            # Check that the replay completed successfully (exit code 0)
            self.assertEqual(cm.exception.code, 0)

        # Verify that the logger was set up
        mock_setup_logger.assert_called()

        # Verify that the correct agent runner was called
        mock_run_gemini.assert_called_once()

        # Inspect the configuration that was passed to the agent runner
        call_args, _ = mock_run_gemini.call_args
        replayed_config = call_args[0]

        self.assertEqual(replayed_config.agent_type, 'gemini')
        self.assertEqual(replayed_config.model, 'gemini-1.5-pro-test')
        self.assertEqual(replayed_config.max_iterations, 15)
        # Check that the CLI arg for verbose override worked
        self.assertEqual(replayed_config.verbose, True)
        self.assertEqual(replayed_config.project_dir, self.project_dir)
        self.assertEqual(replayed_config.spec_file, self.project_dir / 'app_spec.txt')

        # Verify that a new, unique agent_id was generated for this replay run
        self.assertNotEqual(replayed_config.agent_id, run_id)

if __name__ == '__main__':
    unittest.main()
