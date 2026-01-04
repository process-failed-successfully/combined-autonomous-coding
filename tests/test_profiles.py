import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import sys
import asyncio

# Ensure the source code is in the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import main
from shared.config import Config

# Create a dummy config file content
dummy_config_content = """
profiles:
  test_profile:
    agent: "cursor"
    model: "test-model"
    max_iterations: 50
    manager_first: true
    verbose: true

  another_profile:
    agent: "gemini"
    model: "gemini-pro"
"""

class TestAgentProfiles(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.patcher = patch("pathlib.Path.exists", return_value=True)
        self.mock_exists = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("main.AgentClient")
    @patch("main.setup_logger", return_value=(MagicMock(), MagicMock()))
    @patch("main.init_db")
    @patch("main.ensure_git_safe")
    @patch("shared.config_loader.open", new_callable=mock_open, read_data=dummy_config_content)
    @patch("main.ensure_config_exists")
    @patch("main.run_sprint")
    @patch("main.run_gemini")
    @patch("main.run_cursor")
    @patch("main.run_local")
    @patch("main.run_openrouter")
    async def test_profile_loading(self, mock_run_openrouter, mock_run_local, mock_run_cursor, mock_run_gemini, mock_run_sprint, mock_ensure_config, mock_open_file, mock_git_safe, mock_init_db, mock_setup_logger, mock_agent_client):
        """Test that a profile's settings are loaded correctly."""
        with patch.object(sys, "argv", ["main.py", "--profile", "test_profile"]):
            await main()

            mock_run_cursor.assert_called_once()
            config = mock_run_cursor.call_args[0][0]

            self.assertEqual(config.agent_type, "cursor")
            self.assertEqual(config.model, "test-model")
            self.assertEqual(config.max_iterations, 50)
            self.assertTrue(config.run_manager_first)
            self.assertTrue(config.verbose)

    @patch("main.AgentClient")
    @patch("main.setup_logger", return_value=(MagicMock(), MagicMock()))
    @patch("main.init_db")
    @patch("main.ensure_git_safe")
    @patch("shared.config_loader.open", new_callable=mock_open, read_data=dummy_config_content)
    @patch("main.ensure_config_exists")
    @patch("main.run_sprint")
    @patch("main.run_gemini")
    @patch("main.run_cursor")
    @patch("main.run_local")
    @patch("main.run_openrouter")
    async def test_cli_overrides_profile(self, mock_run_openrouter, mock_run_local, mock_run_cursor, mock_run_gemini, mock_run_sprint, mock_ensure_config, mock_open_file, mock_git_safe, mock_init_db, mock_setup_logger, mock_agent_client):
        """Test that CLI arguments override profile settings."""
        with patch.object(sys, "argv", ["main.py", "--profile", "test_profile", "--agent", "gemini", "--model", "override-model"]):
            await main()

            mock_run_gemini.assert_called_once()
            config = mock_run_gemini.call_args[0][0]

            self.assertEqual(config.agent_type, "gemini")
            self.assertEqual(config.model, "override-model")
            self.assertEqual(config.max_iterations, 50) # This should still come from the profile

if __name__ == "__main__":
    unittest.main()
