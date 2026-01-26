import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import tempfile
import shutil

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import DataTable, RichLog
from shared.tui_pull_requests import PullRequestsTab

class TestTUIPullRequests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.tui_pull_requests.load_config_from_file")
    @patch("shared.tui_pull_requests.GitHubClient")
    async def test_load_prs(self, MockGitHubClient, mock_load_config):
        mock_load_config.return_value = {"github_token": "token"}

        mock_client = MockGitHubClient.return_value
        mock_client.list_pull_requests.return_value = [
            {"number": 1, "title": "PR 1", "user": {"login": "user1"}, "created_at": "2023-01-01T00:00:00Z"},
            {"number": 2, "title": "PR 2", "user": {"login": "user2"}, "created_at": "2023-01-02T00:00:00Z"}
        ]

        tab = PullRequestsTab(self.project_dir)

        # Mock widgets
        mock_table = MagicMock(spec=DataTable)
        mock_log = MagicMock(spec=RichLog)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#pr-table": mock_table,
            "#pr-details-log": mock_log
        }.get(selector))

        tab.on_mount()

        # We need to wait for async task
        # Since _fetch_prs is scheduled with asyncio.create_task, we can just wait a bit or use await if we exposed it
        # But _fetch_prs is async method. We can call it directly for testing logic.

        await tab._fetch_prs()

        mock_table.clear.assert_called()
        self.assertEqual(mock_table.add_row.call_count, 2)
        self.assertIn("1", tab.pr_cache)
        self.assertIn("2", tab.pr_cache)

    @patch("shared.tui_pull_requests.load_config_from_file")
    @patch("shared.tui_pull_requests.GitHubClient")
    async def test_show_details(self, MockGitHubClient, mock_load_config):
        mock_load_config.return_value = {"github_token": "token"}
        tab = PullRequestsTab(self.project_dir)

        mock_log = MagicMock(spec=RichLog)
        tab.query_one = MagicMock(return_value=mock_log)

        tab.pr_cache = {
            "1": {
                "number": 1, "title": "PR 1",
                "user": {"login": "user1"},
                "html_url": "url",
                "state": "open",
                "body": "Description"
            }
        }

        tab._show_details("1")

        mock_log.clear.assert_called()
        mock_log.write.assert_any_call("[bold]#1 PR 1[/bold]")

if __name__ == "__main__":
    unittest.main()
