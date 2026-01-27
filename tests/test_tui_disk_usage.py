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

        # Mock UI methods since we aren't running full app
        self.tab.query_one = MagicMock()
        self.tab.notify = MagicMock()
        self.tab._update_tree = MagicMock()
        self.tab._update_table = MagicMock()

        await self.tab._scan_task()

        mock_scan.assert_called_once_with(self.project_dir)
        mock_get_largest.assert_called_once_with(self.project_dir)
        self.tab._update_tree.assert_called_once()
        self.tab._update_table.assert_called_once()
        self.tab.notify.assert_called_with("Scan complete.")

if __name__ == "__main__":
    unittest.main()
