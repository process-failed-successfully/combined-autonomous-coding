import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_disk_usage import DiskUsageTab

class TestDiskUsageTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = DiskUsageTab(self.project_dir)

    def test_initialization(self):
        self.assertEqual(self.tab.project_dir, self.project_dir)
        self.assertEqual(self.tab.scan_data, {})
        self.assertIsNone(self.tab.selected_path)

    @patch("shared.tui_disk_usage.scan_disk_usage")
    @patch("shared.tui_disk_usage.get_largest_files")
    async def test_scan_task(self, mock_get_largest, mock_scan):
        # Mock data
        mock_scan.return_value = {
            "name": "root",
            "size": 1000,
            "type": "dir",
            "children": []
        }
        mock_get_largest.return_value = []

        # Mock UI methods using patch.object to satisfy MyPy
        # query_one returns a widget (or mock), so we need to set its return value
        mock_widget = MagicMock()

        with patch.object(self.tab, 'query_one', return_value=mock_widget) as mock_query_one, \
             patch.object(self.tab, 'notify') as mock_notify, \
             patch.object(self.tab, '_update_tree') as mock_update_tree, \
             patch.object(self.tab, '_update_table') as mock_update_table:

            await self.tab._scan_task()

            mock_scan.assert_called_once_with(self.project_dir)
            mock_get_largest.assert_called_once_with(self.project_dir)

            # verify query_one was called (for button disable/enable)
            # The exact number of calls might vary depending on implementation (start_scan disables, _scan_task re-enables)
            # But here we are calling _scan_task directly which re-enables the button at end
            # It calls self.query_one("#btn-du-refresh").disabled = False
            mock_query_one.assert_called_with("#btn-du-refresh")

            mock_update_tree.assert_called_once()
            mock_update_table.assert_called_once()
            mock_notify.assert_called_with("Scan complete.")

if __name__ == "__main__":
    unittest.main()
