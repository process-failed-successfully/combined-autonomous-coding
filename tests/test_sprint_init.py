import asyncio
import json
import logging
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from agents.shared.sprint import SprintManager
from shared.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_sprint_init")

class TestSprintInit(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.config = Config(
            project_dir=self.test_dir,
            agent_type="gemini",
            sprint_mode=True,
        )
        self.config.sprint_mode = True
        # self.config.feature_list_path is derived from project_dir, so no need to set it.

    async def asyncTearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("agents.shared.sprint.SprintManager._get_agent_runner")
    async def test_ensure_initialized_missing(self, mock_get_runner):
        """Test initialization when file is missing."""
        # Setup mock runner to "create" the file
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_get_runner.return_value = (mock_client, mock_runner)
        
        async def fake_runner(client, prompt, history=None, status_callback=None):
            # Simulate agent writing the file
            self.config.feature_list_path.write_text('[{"name": "Init Feature"}]')
            return "done", "Initialized", []
            
        mock_runner.side_effect = fake_runner

        manager = SprintManager(self.config)
        await manager.ensure_project_initialized()
        
        mock_runner.assert_called()
        self.assertTrue(self.config.feature_list_path.exists())
        self.assertIn("Init Feature", self.config.feature_list_path.read_text())

    @patch("agents.shared.sprint.SprintManager._get_agent_runner")
    async def test_ensure_initialized_empty(self, mock_get_runner):
        """Test initialization when file is empty."""
        self.config.feature_list_path.write_text("") # Empty file
        
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_get_runner.return_value = (mock_client, mock_runner)
        
        async def fake_runner(client, prompt, history=None, status_callback=None):
            self.config.feature_list_path.write_text('[{"name": "Init Feature 2"}]')
            return "done", "Initialized", []
            
        mock_runner.side_effect = fake_runner

        manager = SprintManager(self.config)
        await manager.ensure_project_initialized()
        
        mock_runner.assert_called()
        self.assertIn("Init Feature 2", self.config.feature_list_path.read_text())

if __name__ == "__main__":
    unittest.main()
