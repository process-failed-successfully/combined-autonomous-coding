import unittest
from unittest.mock import patch, AsyncMock
from pathlib import Path
from shared.estimate import run_estimate_logic, _collect_context, get_estimate_prompt
import shutil


class TestEstimate(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("tests/temp_test_estimate_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def test_get_estimate_prompt(self):
        prompt = get_estimate_prompt()
        self.assertIn("Complexity Score", prompt)
        self.assertIn("Estimated Effort", prompt)

    def test_collect_context_no_files(self):
        context = _collect_context(self.project_dir, None)
        self.assertIn("No specific files provided", context)

    def test_collect_context_with_files(self):
        (self.project_dir / "test.py").write_text("print('hello')")
        context = _collect_context(self.project_dir, ["*.py"])
        self.assertIn("File: test.py", context)
        self.assertIn("print('hello')", context)

    @patch("agents.gemini.GeminiAgent")
    async def test_run_estimate_logic_success(self, MockAgent):
        # Setup mock
        mock_instance = MockAgent.return_value
        mock_instance.run_agent_session = AsyncMock(return_value=("success", "Estimation Result", []))

        success = await run_estimate_logic(
            feature_description="Add login",
            project_dir=self.project_dir,
            files=None
        )

        self.assertTrue(success)
        mock_instance.run_agent_session.assert_called_once()

        # Verify prompt construction
        args, _ = mock_instance.run_agent_session.call_args
        prompt = args[0]
        self.assertIn("Add login", prompt)

    @patch("agents.gemini.GeminiAgent")
    async def test_run_estimate_logic_error(self, MockAgent):
        mock_instance = MockAgent.return_value
        mock_instance.run_agent_session = AsyncMock(return_value=("error", "Some error", []))

        success = await run_estimate_logic(
            feature_description="Add login",
            project_dir=self.project_dir
        )

        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
