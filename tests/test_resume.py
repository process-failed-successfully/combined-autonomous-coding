import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import asyncio
from shared.resume import ResumeGenerator

class TestResumeGenerator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.generator = ResumeGenerator(self.project_dir)

    @patch("shared.resume.subprocess.run")
    @patch("shared.resume.shutil.which")
    @patch("pathlib.Path.is_dir")
    def test_collect_git_stats(self, mock_is_dir, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/git"
        mock_is_dir.return_value = True

        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="123\n"),
            MagicMock(returncode=0, stdout="10\tAlice\n5\tBob\n"),
            MagicMock(returncode=0, stdout="2023-01-01\n"),
            MagicMock(returncode=0, stdout="2023-12-31\n"),
        ]

        stats = self.generator.collect_git_stats()

        self.assertEqual(stats["commit_count"], 123)
        self.assertEqual(len(stats["contributors"]), 2)
        self.assertEqual(stats["contributors"][0]["name"], "Alice")
        self.assertEqual(stats["start_date"], "2023-01-01")
        self.assertEqual(stats["last_update"], "2023-12-31")

    @patch("shared.resume.DependencyAnalyzer")
    def test_detect_tech_stack(self, MockAnalyzer):
        mock_instance = MockAnalyzer.return_value
        mock_instance.scan.return_value = {
            "python": [{"dependencies": [{"name": "flask"}]}],
            "node": []
        }
        self.generator.analyzer = mock_instance

        stack = self.generator.detect_tech_stack()
        self.assertIn("Python", stack["languages"])
        self.assertIn("flask", stack["libraries"])

    def test_get_features(self):
        fake_features = '["Feature A", "Feature B"]'
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=fake_features):
            features = self.generator.get_features()
            self.assertEqual(features, ["Feature A", "Feature B"])

    @patch("shared.resume.GeminiAgent")
    async def test_generate_executive_summary(self, MockAgent):
        # run_agent_session is async, so we use AsyncMock
        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock(return_value=(True, "This is a summary.", []))

        summary = await self.generator.generate_executive_summary()
        self.assertEqual(summary, "This is a summary.")

    @patch("shared.resume.ResumeGenerator.collect_git_stats")
    @patch("shared.resume.ResumeGenerator.detect_tech_stack")
    @patch("shared.resume.ResumeGenerator.get_features")
    @patch("shared.resume.ResumeGenerator.generate_executive_summary")
    async def test_render(self, mock_summary, mock_features, mock_stack, mock_stats):
        mock_stats.return_value = {"commit_count": 100}
        mock_stack.return_value = {"languages": ["Python"], "libraries": []}
        mock_features.return_value = ["Feature 1"]
        mock_summary.return_value = "AI Summary"

        md = await self.generator.render()

        self.assertIn("# Project Resume:", md)
        self.assertIn("AI Summary", md)
        self.assertIn("Python", md)
        self.assertIn("Total Commits", md)
        self.assertIn("100", md)

if __name__ == "__main__":
    unittest.main()
