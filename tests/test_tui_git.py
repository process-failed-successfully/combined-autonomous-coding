import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, DataTable, RichLog
from shared.tui_git import GitTab

class TestTUIGit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock git functions
        self.patcher_log = patch("shared.tui_git.get_git_log")
        self.mock_get_log = self.patcher_log.start()

        self.patcher_details = patch("shared.tui_git.get_commit_details")
        self.mock_get_details = self.patcher_details.start()

        self.patcher_status = patch("shared.tui_git.get_git_status")
        self.mock_get_status = self.patcher_status.start()

        self.patcher_stashes = patch("shared.tui_git.get_git_stash_list")
        self.mock_get_stashes = self.patcher_stashes.start()

    def tearDown(self):
        self.patcher_log.stop()
        self.patcher_details.stop()
        self.patcher_status.stop()
        self.patcher_stashes.stop()
        shutil.rmtree(self.test_dir)

    async def test_git_tab_init(self):
        """Test the git tab initialization."""
        # We can't run full app test easily without more setup, so we test the widget logic
        tab = GitTab(self.project_dir)
        self.assertIsInstance(tab, GitTab)

    async def test_git_tab_logic(self):
        """Test logic of GitTab isolated."""

        # Setup mock data
        self.mock_get_log.return_value = [
            {"hash": "abc1234", "author": "Alice", "date": "2023-01-01", "message": "Initial commit"},
            {"hash": "def5678", "author": "Bob", "date": "2023-01-02", "message": "Fix bug"}
        ]

        self.mock_get_status.return_value = [
            {"path": "file1.py", "status_code": "M ", "staged": True}
        ]

        self.mock_get_stashes.return_value = []

        tab = GitTab(self.project_dir)
        # Mock notify
        tab.notify = MagicMock()

        # Mock UI elements
        mock_history_table = MagicMock(spec=DataTable)
        mock_status_table = MagicMock(spec=DataTable)
        mock_stash_table = MagicMock(spec=DataTable)
        mock_details = MagicMock(spec=RichLog)

        # Mock buttons
        mock_btn_pop = MagicMock()
        mock_btn_apply = MagicMock()
        mock_btn_drop = MagicMock()
        mock_diff_view = MagicMock(spec=RichLog)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#git-log-table": mock_history_table,
            "#git-status-table": mock_status_table,
            "#git-stash-table": mock_stash_table,
            "#git-details-view": mock_details,
            "#btn-stash-pop": mock_btn_pop,
            "#btn-stash-apply": mock_btn_apply,
            "#btn-stash-drop": mock_btn_drop,
            "#git-stash-diff-view": mock_diff_view
        }.get(selector, MagicMock()))

        # Test on_mount (load_history, load_status, load_stashes)
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

        # Verify stash loading
        mock_stash_table.add_columns.assert_called()

    async def test_stash_logic(self):
        """Test stash loading and selection."""
        self.mock_get_stashes.return_value = [{"index": "0", "name": "stash@{0}", "message": "WIP"}]

        tab = GitTab(self.project_dir)
        tab.notify = MagicMock()

        mock_stash_table = MagicMock(spec=DataTable)
        mock_btn_pop = MagicMock()
        mock_btn_apply = MagicMock()
        mock_btn_drop = MagicMock()
        mock_diff_view = MagicMock(spec=RichLog)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#git-stash-table": mock_stash_table,
            "#btn-stash-pop": mock_btn_pop,
            "#btn-stash-apply": mock_btn_apply,
            "#btn-stash-drop": mock_btn_drop,
            "#git-stash-diff-view": mock_diff_view
        }.get(selector, MagicMock()))

        tab.load_stashes()
        mock_stash_table.add_row.assert_called_with("stash@{0}", "WIP", key="stash@{0}")

        # Test selection
        with patch("shared.tui_git.get_stash_show") as mock_show:
            mock_show.return_value = "diff content"

            event = MagicMock()
            event.row_key.value = "stash@{0}"

            tab.on_stash_selected(event)

            self.assertEqual(tab.selected_stash, "stash@{0}")
            # Buttons enabled
            self.assertFalse(mock_btn_pop.disabled)
            self.assertFalse(mock_btn_apply.disabled)
            self.assertFalse(mock_btn_drop.disabled)

            mock_show.assert_called_with(self.project_dir, "stash@{0}")
            # Verify diff written
            # diff is written wrapped in Syntax
            mock_diff_view.write.assert_called()

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

        # Mock table.get_row to return the data for the selected row
        mock_table.get_row.return_value = ["abc1234", "2023-01-01", "Alice", "Initial commit"]

        # Mock details response
        self.mock_get_details.return_value = "commit abc1234\nAuthor: Alice\n\nInitial commit"

        # Simulate selection event
        event = MagicMock(spec=DataTable.RowSelected)
        event.row_key = "row1"

        # Call handler directly
        tab.on_history_selected(event)

        mock_table.get_row.assert_called_with("row1")
        self.mock_get_details.assert_called_with(self.project_dir, "abc1234")
        mock_details.clear.assert_called()
        mock_details.write.assert_called_with("commit abc1234\nAuthor: Alice\n\nInitial commit")

if __name__ == "__main__":
    unittest.main()
