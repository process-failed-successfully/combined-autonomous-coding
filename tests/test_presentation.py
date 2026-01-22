import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from shared.presentation import PresentationGenerator


class TestPresentationGenerator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "test_project"
        self.project_dir.mkdir()

        # Create dummy artifacts
        (self.project_dir / "app_spec.txt").write_text("Build a cool app.", encoding="utf-8")
        (self.project_dir / "feature_list.json").write_text('[{"description": "Login", "passes": true}]', encoding="utf-8")
        (self.project_dir / "final_metrics.txt").write_text("Total Execution Time (s): 10.5", encoding="utf-8")

        # Mock git (since we are in a temp dir)
        self.git_patcher = patch("shutil.which")
        self.mock_git = self.git_patcher.start()
        self.mock_git.return_value = None  # Simulate no git to simplify tests

    def tearDown(self):
        self.git_patcher.stop()
        shutil.rmtree(self.test_dir)

    async def test_collect_context(self):
        generator = PresentationGenerator(self.project_dir)
        context = generator.collect_context()

        self.assertIn("Project Name: test_project", context)
        self.assertIn("Build a cool app", context)
        self.assertIn("Login", context)
        self.assertIn("Execution Time: 10.5s", context)

    @patch("agents.gemini.GeminiAgent.run_agent_session", new_callable=AsyncMock)
    async def test_generate(self, mock_run_agent):
        mock_run_agent.return_value = ("done", "---\n# Title Slide\n---\n# Slide 2", [])

        output_file = self.project_dir / "my_presentation.md"
        generator = PresentationGenerator(self.project_dir)

        success = await generator.generate(output_file)

        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("# Title Slide", content)

        # Verify prompt contained context
        args, _ = mock_run_agent.call_args
        prompt = args[0]
        self.assertIn("Build a cool app", prompt)
        self.assertIn("Login", prompt)


if __name__ == "__main__":
    unittest.main()
