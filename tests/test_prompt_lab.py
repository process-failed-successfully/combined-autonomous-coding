import unittest
from unittest.mock import patch, AsyncMock
from pathlib import Path
import tempfile
import shutil
from shared.prompt_lab import PromptLabManager


class TestPromptLabManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.manager = PromptLabManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_experiments_empty(self):
        experiments = self.manager.list_experiments()
        self.assertEqual(experiments, [])

    def test_save_and_load_experiment(self):
        data = {
            "system_prompt": "Sys",
            "user_prompt": "User",
            "agents": ["gemini"]
        }
        self.manager.save_experiment("test_exp", data)

        experiments = self.manager.list_experiments()
        self.assertEqual(experiments, ["test_exp"])

        loaded = self.manager.load_experiment("test_exp")
        self.assertEqual(loaded, data)

    def test_delete_experiment(self):
        data = {"foo": "bar"}
        self.manager.save_experiment("to_delete", data)
        self.assertTrue(self.manager.delete_experiment("to_delete"))
        self.assertEqual(self.manager.list_experiments(), [])
        self.assertFalse(self.manager.delete_experiment("non_existent"))

    @patch("shared.prompt_lab.GeminiAgent")
    @patch("shared.prompt_lab.CursorAgent")
    async def test_run_experiment(self, MockCursor, MockGemini):
        # Setup mocks
        mock_gemini_instance = AsyncMock()
        mock_gemini_instance.run_agent_session.return_value = (True, "Gemini Response", [])
        MockGemini.return_value = mock_gemini_instance

        mock_cursor_instance = AsyncMock()
        mock_cursor_instance.run_agent_session.return_value = (True, "Cursor Response", [])
        MockCursor.return_value = mock_cursor_instance

        # Run
        results = await self.manager.run_experiment(
            system_prompt="Sys",
            user_prompt="User",
            agent_types=["gemini", "cursor"]
        )

        # Assertions
        self.assertEqual(results["gemini"], "Gemini Response")
        self.assertEqual(results["cursor"], "Cursor Response")

        # Verify calls
        # Prompt should be combined
        expected_prompt = "System:\nSys\n\nUser:\nUser"
        mock_gemini_instance.run_agent_session.assert_called_with(expected_prompt)
        mock_cursor_instance.run_agent_session.assert_called_with(expected_prompt)


if __name__ == "__main__":
    unittest.main()
