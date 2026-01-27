import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.widgets import DataTable, Button, RichLog
from shared.tui_trash import TrashTab

class TestTrashTab(unittest.IsolatedAsyncioTestCase):
    async def test_trash_tab_mount(self):
        # Mock TrashManager
        with patch('shared.tui_trash.TrashManager') as MockManager:
            instance = MockManager.return_value
            instance.list_trash.return_value = [
                {"id": "t1", "time": "2023-01-01", "original_path": "/path/to/file", "filename": "file", "is_dir": False}
            ]

            project_dir = Path("/tmp")
            tab = TrashTab(project_dir)

            # Setup mock query_one
            tab.query_one = MagicMock()
            table_mock = MagicMock(spec=DataTable)
            log_mock = MagicMock(spec=RichLog)

            def side_effect(selector, type=None):
                if "#trash-table" in selector: return table_mock
                if "#trash-log" in selector: return log_mock
                if "#btn-trash-restore" in selector: return MagicMock(spec=Button)
                if "#btn-trash-delete" in selector: return MagicMock(spec=Button)
                return MagicMock()

            tab.query_one.side_effect = side_effect

            # Call load_trash logic
            tab.load_trash()

            # Verify list_trash called
            instance.list_trash.assert_called()

            # Verify table populated
            table_mock.clear.assert_called()
            table_mock.add_row.assert_called_with(
                "2023-01-01", "/path/to/file", "file", key="t1"
            )

    async def test_restore_action(self):
        with patch('shared.tui_trash.TrashManager') as MockManager:
            instance = MockManager.return_value
            instance.restore.return_value = True

            tab = TrashTab(Path("/tmp"))
            tab.selected_trash_id = "t1"
            tab.notify = MagicMock()
            tab.load_trash = MagicMock() # prevent recursion

            tab.restore_selected()

            instance.restore.assert_called_with("t1")
            tab.notify.assert_called_with("Restored successfully.")
            tab.load_trash.assert_called()

    async def test_empty_trash_action(self):
        with patch('shared.tui_trash.TrashManager') as MockManager:
            instance = MockManager.return_value

            tab = TrashTab(Path("/tmp"))
            tab.notify = MagicMock()
            tab.load_trash = MagicMock()

            tab.empty_trash()

            instance.empty_trash.assert_called()
            tab.notify.assert_called_with("Trash emptied.")
            tab.load_trash.assert_called()
