import sys
from pathlib import Path
# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
# noqa: E402
from textual.widgets import DirectoryTree, DataTable, Input, RichLog
from shared.tui_archive import ArchiveLabTab

class TestArchiveLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = ArchiveLabTab(self.project_dir)
        # Mock the manager
        self.tab.manager = MagicMock()
        # Mock app for notify
        with patch('shared.tui_archive.ArchiveLabTab.app', new_callable=MagicMock) as mock_app:
             self.tab.app = mock_app # This might not work if accessed as property.
             # Textual widgets access .app property. We can patch it on the instance if needed,
             # but usually it's better to patch query_one and not rely on app being present unless mounted.
             # In my code I use self.notify which is a method on Widget/App.
             # Actually self.notify delegates to self.app.notify if available or handles it.
             pass

        # Patch notify on the tab instance itself to avoid App dependency issues
        self.tab.notify = MagicMock()

    async def test_file_selected_valid_archive(self):
        # Setup
        event = MagicMock()
        event.path = MagicMock(spec=Path)
        event.path.is_file.return_value = True
        event.path.suffix = ".zip" # Important for validation logic
        event.path.suffixes = [".zip"]
        event.path.name = "test.zip"

        # Mock manager list_contents
        self.tab.manager.list_contents.return_value = [
            {"name": "file1.txt", "size": 100, "modified": "2023-01-01T12:00:00", "type": "file"}
        ]
        self.tab.manager.format_bytes.return_value = "100 B"

        # Mock widgets
        with patch.object(self.tab, 'query_one') as mock_query_one:
            # Setup mocks for widgets returned by query_one
            mock_table = MagicMock(spec=DataTable)
            mock_log = MagicMock(spec=RichLog)
            mock_btn = MagicMock()
            mock_lbl = MagicMock()

            # Use side_effect to return specific mocks for IDs
            def side_effect(selector, type=None):
                if "#archive-table" in selector: return mock_table
                if "#archive-log" in selector: return mock_log
                if "#btn-extract" in selector: return mock_btn
                if "#lbl-archive-name" in selector: return mock_lbl
                return MagicMock()

            mock_query_one.side_effect = side_effect

            # Execute
            self.tab.on_file_selected(event)

            # Verify
            self.tab.manager.list_contents.assert_called_with(event.path)
            mock_table.clear.assert_called()
            mock_table.add_row.assert_called()
            # We can't verify property setting on MagicMock easily unless we inspect it
            # But the code sets disabled=False
            self.assertEqual(mock_btn.disabled, False)

    async def test_extract_archive(self):
        self.tab.selected_archive = Path("/tmp/test.zip")

        with patch.object(self.tab, 'query_one') as mock_query_one:
            mock_input = MagicMock(spec=Input)
            mock_input.value = "/output_dir" # Test sanitization
            mock_log = MagicMock(spec=RichLog)

            def side_effect(selector, type=None):
                if "#extract-dest" in selector: return mock_input
                if "#archive-log" in selector: return mock_log
                return MagicMock()

            mock_query_one.side_effect = side_effect

            self.tab.manager.extract.return_value = "/tmp/test_project/output_dir"

            # Execute
            await self.tab.extract_archive()

            # Verify
            # to_thread calls the function, so manager.extract should be called
            self.tab.manager.extract.assert_called_with(self.tab.selected_archive, self.project_dir / "output_dir")
            mock_log.write.assert_called()
            self.tab.notify.assert_called_with("Extraction complete.")

    async def test_create_archive(self):
        with patch.object(self.tab, 'query_one') as mock_query_one:
            mock_name = MagicMock(spec=Input)
            mock_name.value = "/new.zip" # Test sanitization
            mock_files = MagicMock(spec=Input)
            mock_files.value = "/file1.txt, dir1/" # Test sanitization
            mock_log = MagicMock(spec=RichLog)

            def side_effect(selector, type=None):
                if "#create-name" in selector: return mock_name
                if "#create-files" in selector: return mock_files
                if "#create-log" in selector: return mock_log
                return MagicMock()

            mock_query_one.side_effect = side_effect

            self.tab.manager.create.return_value = "/tmp/test_project/new.zip"

            # Execute
            await self.tab.create_archive()

            # Verify
            expected_files = [self.project_dir / "file1.txt", self.project_dir / "dir1/"]
            self.tab.manager.create.assert_called()
            # check args
            call_args = self.tab.manager.create.call_args
            self.assertEqual(call_args[0][0], self.project_dir / "new.zip")
            self.assertEqual(call_args[0][1], expected_files)

            mock_log.write.assert_called()
            self.tab.notify.assert_called_with("Archive created.")

if __name__ == '__main__':
    unittest.main()
