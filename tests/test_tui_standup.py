import unittest
import shutil
import tempfile
from unittest.mock import patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button
from shared.tui_standup import StandupTab


class StandupTestApp(App):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield StandupTab(self.project_dir)


class TestTUIStandup(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    async def asyncTearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.tui_standup.get_commits_since")
    async def test_fetch_commits(self, mock_get_commits):
        # Setup mock
        mock_get_commits.return_value = [
            {"date": "2023-10-26 10:00", "hash": "abc123456", "subject": "Test Commit", "author": "Tester"}
        ]

        app = StandupTestApp(self.test_dir)
        async with app.run_test():
            tab = app.query_one(StandupTab)
            btn = tab.query_one("#btn-standup-fetch", Button)

            # Simulate press directly
            await tab.on_button_pressed(Button.Pressed(btn))

            # Verify mock called
            mock_get_commits.assert_called_with(self.test_dir, "24 hours ago", None)

            # Verify table
            table = tab.query_one("#standup-table", DataTable)
            self.assertEqual(table.row_count, 1)
            self.assertEqual(table.get_row_at(0)[2], "Test Commit")

    @patch("shared.tui_standup.get_commits_since")
    @patch("shared.tui_standup.generate_standup_report")
    async def test_generate_report(self, mock_gen_report, mock_get_commits):
        mock_get_commits.return_value = [
            {"date": "2023-10-26 10:00", "hash": "abc123456", "subject": "Test Commit", "author": "Tester"}
        ]
        mock_gen_report.return_value = "**Report Content**"

        app = StandupTestApp(self.test_dir)
        async with app.run_test():
            tab = app.query_one(StandupTab)

            # Must fetch first to enable generate
            btn_fetch = tab.query_one("#btn-standup-fetch", Button)
            await tab.on_button_pressed(Button.Pressed(btn_fetch))

            # Click generate
            btn_gen = tab.query_one("#btn-standup-generate", Button)
            await tab.on_button_pressed(Button.Pressed(btn_gen))

            # Verify mock called
            mock_gen_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
