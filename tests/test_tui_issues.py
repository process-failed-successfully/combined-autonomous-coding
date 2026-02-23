import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import tempfile
import shutil
import subprocess

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import DataTable, RichLog, Select
from shared.tui_issues import IssuesLabTab

class TestTUIIssues(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.tui_issues.load_config_from_file")
    @patch("shared.tui_issues.GitHubClient")
    async def test_load_issues(self, MockGitHubClient, mock_load_config):
        mock_load_config.return_value = {"github_token": "token"}

        mock_client = MockGitHubClient.return_value
        mock_client.get_issues.return_value = [
            {"number": 1, "title": "Issue 1", "user": {"login": "user1"}, "state": "open", "labels": []},
            {"number": 2, "title": "Issue 2", "user": {"login": "user2"}, "state": "open", "labels": [{"name": "bug"}]}
        ]

        tab = IssuesLabTab(self.project_dir)

        # Mock widgets
        mock_table = MagicMock(spec=DataTable)
        mock_log = MagicMock(spec=RichLog)
        mock_select = MagicMock(spec=Select)
        mock_select.value = "open"

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#issue-table": mock_table,
            "#issue-details-log": mock_log,
            "#issue-state-select": mock_select
        }.get(selector))

        tab.notify = MagicMock()

        tab.on_mount()

        await tab._fetch_issues("open")

        mock_table.clear.assert_called()
        self.assertEqual(mock_table.add_row.call_count, 2)
        self.assertIn("1", tab.issues_cache)
        self.assertIn("2", tab.issues_cache)

    @patch("shared.tui_issues.load_config_from_file")
    @patch("shared.tui_issues.GitHubClient")
    async def test_show_details(self, MockGitHubClient, mock_load_config):
        mock_load_config.return_value = {"github_token": "token"}
        tab = IssuesLabTab(self.project_dir)

        mock_log = MagicMock(spec=RichLog)
        tab.query_one = MagicMock(return_value=mock_log)

        tab.issues_cache = {
            "1": {
                "number": 1, "title": "Issue 1",
                "user": {"login": "user1"},
                "html_url": "url",
                "state": "open",
                "body": "Description"
            }
        }

        tab._show_details("1")

        mock_log.clear.assert_called()
        mock_log.write.assert_any_call("[bold]#1 Issue 1[/bold]")

    @patch("shared.tui_issues.load_config_from_file")
    @patch("shared.tui_issues.GitHubClient")
    @patch("subprocess.run")
    async def test_start_work(self, mock_subprocess, MockGitHubClient, mock_load_config):
        mock_load_config.return_value = {"github_token": "token"}
        tab = IssuesLabTab(self.project_dir)

        # Mock notify
        tab.notify = MagicMock()
        tab.query_one = MagicMock(return_value=MagicMock()) # Mock RichLog

        tab.issues_cache = {
            "1": {
                "number": 1, "title": "Fix Bug",
                "user": {"login": "user1"},
            }
        }
        tab.selected_issue_number = "1"

        # Mock subprocess to simulate branch check failure (branch doesn't exist)
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "cmd"), # rev-parse fails
            MagicMock() # checkout -b succeeds
        ]

        await tab.on_start_work()

        # Verify branch name generation
        # issue-1-fix-bug
        # We need to check call args of subprocess.run
        # The calls happen in _create_branch_logic which is awaited in a thread.
        # Since we mocked subprocess.run globally, it should capture calls.

        self.assertTrue(mock_subprocess.called)

        # Find the call with checkout -b
        found = False
        for call in mock_subprocess.call_args_list:
            args, _ = call
            cmd_list = args[0]
            if "checkout" in cmd_list and "-b" in cmd_list:
                self.assertIn("issue-1-fix-bug", cmd_list)
                found = True
                break

        self.assertTrue(found, "Branch creation command not found")

if __name__ == "__main__":
    unittest.main()
