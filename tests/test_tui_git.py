import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, DataTable, RichLog
from shared.tui import AgentTUI, GitTab

class TestTUIGit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock git functions
        self.patcher_log = patch("shared.tui.get_git_log")
        self.mock_get_log = self.patcher_log.start()

        self.patcher_details = patch("shared.tui.get_commit_details")
        self.mock_get_details = self.patcher_details.start()

    def tearDown(self):
        self.patcher_log.stop()
        self.patcher_details.stop()
        shutil.rmtree(self.test_dir)

    async def test_git_tab_structure(self):
        """Test the git tab structure."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Check if TabPane exists
            self.assertTrue(app.query_one("#tab-git"))

    @patch("shared.tui.get_git_status")
    async def test_git_tab_logic(self, mock_get_status):
        """Test logic of GitTab isolated."""

        # Setup mock data
        self.mock_get_log.return_value = [
            {"hash": "abc1234", "author": "Alice", "date": "2023-01-01", "message": "Initial commit"},
            {"hash": "def5678", "author": "Bob", "date": "2023-01-02", "message": "Fix bug"}
        ]

        mock_get_status.return_value = [
            {"path": "file1.py", "status_code": "M ", "staged": True}
        ]

        tab = GitTab(self.project_dir)
        # Mock notify
        tab.notify = MagicMock()

        # Mock UI elements
        mock_history_table = MagicMock(spec=DataTable)
        mock_status_table = MagicMock(spec=DataTable)
        mock_details = MagicMock(spec=RichLog)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#git-log-table": mock_history_table,
            "#git-status-table": mock_status_table,
            "#git-details-view": mock_details
        }.get(selector))

        # Test on_mount (load_history)
        tab.on_mount()

        self.mock_get_log.assert_called_once_with(self.project_dir)
        mock_history_table.add_columns.assert_called()
        mock_history_table.clear.assert_called()

        # Verify history row addition
        add_row_calls = mock_history_table.add_row.call_args_list
        self.assertEqual(len(add_row_calls), 2)
        self.assertEqual(add_row_calls[0][0][0], "abc1234")

        # Verify status row addition
        mock_status_table.add_row.assert_called()

    async def test_git_selection_logic(self):
        """Test row selection logic."""
        tab = GitTab(self.project_dir)
        tab.notify = MagicMock()

        mock_table = MagicMock(spec=DataTable)
        mock_details = MagicMock(spec=RichLog)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#git-log-table": mock_table,
            "#git-details-view": mock_details
        }.get(selector))

        # Setup interaction
        # When a row is selected, we get a RowSelected event.
        # The handler calls table.get_row(event.row_key)

        # Mock table.get_row to return the data for the selected row
        mock_table.get_row.return_value = ["abc1234", "2023-01-01", "Alice", "Initial commit"]

        # Mock details response
        self.mock_get_details.return_value = "commit abc1234\nAuthor: Alice\n\nInitial commit"

        # Simulate selection event
        event = MagicMock(spec=DataTable.RowSelected)
        event.row_key = "row1"

        # Call handler directly since we can't easily emit event in isolation without full app
        tab.on_history_selected(event)

        mock_table.get_row.assert_called_with("row1")
        self.mock_get_details.assert_called_with(self.project_dir, "abc1234")
        mock_details.clear.assert_called()
        mock_details.write.assert_called_with("commit abc1234\nAuthor: Alice\n\nInitial commit")

if __name__ == "__main__":
    unittest.main()
