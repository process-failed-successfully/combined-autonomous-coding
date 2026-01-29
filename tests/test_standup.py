import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

class TestStandup(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Patch sys.modules to mock missing dependencies
        self.modules_patcher = patch.dict(sys.modules, {
            'google': MagicMock(),
            'google.generativeai': MagicMock(),
            'psutil': MagicMock(),
            'docker': MagicMock(),
            'prometheus_client': MagicMock(),
            'requests': MagicMock(),
            'jira': MagicMock(),
            'tenacity': MagicMock(),
            'openai': MagicMock()
        })
        self.modules_patcher.start()

        # Import module under test
        import shared.standup
        self.standup = shared.standup

    def tearDown(self):
        self.modules_patcher.stop()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_get_commits_since(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/git"

        # Mock git log output
        output = """hash1|author1|2023-10-27|feat: something
Body line 1
Body line 2
---COMMIT_END---
hash2|author2|2023-10-26|fix: bug | pipe
Body line 1
---COMMIT_END---
"""
        mock_run.return_value = MagicMock(stdout=output, returncode=0)

        commits = self.standup.get_commits_since(Path("."), "24 hours ago")

        self.assertEqual(len(commits), 2)
        self.assertEqual(commits[0]['hash'], 'hash1')
        self.assertEqual(commits[0]['subject'], 'feat: something')
        self.assertEqual(commits[1]['hash'], 'hash2')
        # Test the fix for pipe in subject
        self.assertEqual(commits[1]['subject'], 'fix: bug | pipe')

    @patch('shared.standup.GeminiAgent')
    @patch('shared.standup.get_commits_since')
    async def test_run_standup_logic(self, mock_get_commits, MockAgent):
        # Setup mocks
        mock_get_commits.return_value = [
            {'hash': 'h1', 'author': 'me', 'date': 'today', 'subject': 'feat: a', 'body': ''}
        ]

        mock_agent_instance = MockAgent.return_value
        mock_agent_instance.run_agent_session = AsyncMock()

        args = MagicMock()
        args.project_dir = Path(".")
        args.since = "yesterday"
        args.author = None
        args.agent = "gemini"
        args.model = None
        args.verbose = False

        # Run logic
        result = await self.standup.run_standup_logic(args)

        self.assertTrue(result)
        mock_agent_instance.run_agent_session.assert_called_once()

        # Verify prompt contains commit info
        call_args = mock_agent_instance.run_agent_session.call_args[0][0]
        self.assertIn("feat: a", call_args)

    @patch('shared.standup.get_commits_since')
    async def test_run_standup_logic_no_commits(self, mock_get_commits):
        mock_get_commits.return_value = []

        args = MagicMock()
        args.project_dir = Path(".")
        args.since = "yesterday"
        args.author = None

        result = await self.standup.run_standup_logic(args)

        self.assertTrue(result) # Should return True (success) even if no commits

    async def test_generate_standup_report_empty(self):
        report = await self.standup.generate_standup_report([], "gemini")
        self.assertEqual(report, "No commits found.")

    @patch('shared.standup.GeminiAgent')
    async def test_generate_standup_report_success(self, MockAgent):
        # Mock agent behavior
        mock_instance = MockAgent.return_value
        mock_instance.run_agent_session = AsyncMock()

        async def side_effect(prompt):
            print("Generated Report Content")

        mock_instance.run_agent_session.side_effect = side_effect

        commits = [{"date": "d", "hash": "h", "subject": "s", "body": "b"}]
        report = await self.standup.generate_standup_report(commits, "gemini")

        self.assertIn("Generated Report Content", report)

if __name__ == '__main__':
    unittest.main()
