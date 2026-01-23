import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, ListView, RichLog, Input, TextArea, ListItem
from shared.tui import PlaygroundTab

class TestTUIPlayground(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock PlaygroundManager
        self.patcher_manager = patch("shared.tui.PlaygroundManager")
        self.mock_manager_cls = self.patcher_manager.start()
        self.mock_manager = self.mock_manager_cls.return_value

    def tearDown(self):
        self.patcher_manager.stop()
        shutil.rmtree(self.test_dir)

    async def test_playground_tab_structure(self):
        """Test the playground tab structure."""
        tab = PlaygroundTab(self.project_dir)
        self.assertIsNotNone(tab)

    async def test_load_files(self):
        """Test loading files into the list view."""
        file1 = MagicMock()
        file1.name = "script1.py"
        file2 = MagicMock()
        file2.name = "script2.py"
        self.mock_manager.list_files.return_value = [file1, file2]

        tab = PlaygroundTab(self.project_dir)
        tab.notify = MagicMock()

        mock_list_view = MagicMock(spec=ListView)
        # Mocking query_one to return the ListView
        tab.query_one = MagicMock(return_value=mock_list_view)

        tab.load_files()

        self.mock_manager.list_files.assert_called_once()
        self.assertEqual(mock_list_view.append.call_count, 2)

    async def test_create_file(self):
        """Test creating a new file."""
        tab = PlaygroundTab(self.project_dir)
        tab.notify = MagicMock()
        tab.load_files = MagicMock()
        tab.load_file_content = MagicMock()

        mock_input = MagicMock(spec=Input)
        mock_input.value = "new_script.py"
        tab.query_one = MagicMock(return_value=mock_input)

        mock_path = MagicMock()
        mock_path.name = "new_script.py"
        self.mock_manager.create.return_value = mock_path

        await tab.create_file()

        self.mock_manager.create.assert_called_with("new_script.py")
        tab.load_files.assert_called()
        tab.load_file_content.assert_called_with("new_script.py")
        self.assertEqual(mock_input.value, "")

    async def test_run_file(self):
        """Test running a file."""
        tab = PlaygroundTab(self.project_dir)
        tab.current_file = "script.py"
        tab.notify = MagicMock()
        tab.save_file = AsyncMock()

        mock_log = MagicMock(spec=RichLog)
        tab.query_one = MagicMock(return_value=mock_log)

        # Mock manager.run to return success
        self.mock_manager.run.return_value = (True, "Output")

        await tab.run_file()

        tab.save_file.assert_awaited()
        self.mock_manager.run.assert_called_with("script.py", capture_output=True)
        mock_log.write.assert_called()

if __name__ == "__main__":
    unittest.main()
