import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, RichLog, Select, DirectoryTree, Button  # noqa: E402
from textual.app import App, ComposeResult
from shared.tui import RefactorTab  # noqa: E402

# Helper App to mount the widget for testing
class RefactorTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
        self.tab = RefactorTab(project_dir)

    def compose(self) -> ComposeResult:
        yield self.tab

class TestTUIRefactor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Create a dummy file
        self.target_file = self.project_dir / "target.py"
        self.target_file.write_text("print('hello')")

        # Mock RefactorManager
        self.patcher_manager = patch("shared.tui.RefactorManager")
        self.mock_manager_cls = self.patcher_manager.start()
        self.mock_manager = self.mock_manager_cls.return_value

    def tearDown(self):
        self.patcher_manager.stop()
        shutil.rmtree(self.test_dir)

    async def test_compose(self):
        """Test the UI composition."""
        app = RefactorTestApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.tab
            self.assertIsNotNone(tab)
            self.assertIsNotNone(tab.query_one("#refactor-file-tree"))
            self.assertIsNotNone(tab.query_one("#refactor-instruction"))
            self.assertIsNotNone(tab.query_one("#refactor-diff-log"))

    async def test_select_file(self):
        """Test file selection logic."""
        app = RefactorTestApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.tab

            # Simulate selection manually calling the handler
            # Constructing the event is hard because it requires internal node objects
            # So we manually invoke the handler

            # Mock event
            mock_event = MagicMock()
            mock_event.path = self.target_file
            # self.target_file is a real Path, so is_file() works

            tab.on_directory_tree_file_selected(mock_event)

            self.assertEqual(tab.selected_file, self.target_file)
            self.assertFalse(tab.query_one("#btn-refactor-preview").disabled)

    async def test_preview_refactor(self):
        """Test preview generation."""
        app = RefactorTestApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.tab
            # Mock notify to prevent actual notifications
            tab.notify = MagicMock()

            # Setup state
            tab.selected_file = self.target_file
            tab.query_one("#refactor-instruction").value = "Add logging"

            # Mock manager response
            self.mock_manager.refactor_file = AsyncMock(return_value={
                "original_content": "print('hello')",
                "new_content": "print('hello')\nprint('log')",
                "diff": "diff content",
                "changed": True
            })

            # Enable the button (normally done by file selection)
            tab.query_one("#btn-refactor-preview").disabled = False

            # Run preview
            await tab.preview_refactor()

            self.mock_manager.refactor_file.assert_awaited_once()

            # Verify UI update
            self.assertFalse(tab.query_one("#btn-refactor-apply").disabled)
            self.assertEqual(tab.preview_data["new_content"], "print('hello')\nprint('log')")

    async def test_apply_changes(self):
        """Test applying changes."""
        app = RefactorTestApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.tab
            tab.notify = MagicMock()

            # Setup state
            tab.selected_file = self.target_file
            tab.preview_data = {
                "new_content": "new code"
            }

            # Run apply
            tab.apply_changes()

            self.mock_manager.apply_changes.assert_called_with(
                self.target_file, "new code"
            )
            self.assertTrue(tab.query_one("#btn-refactor-apply").disabled)
            self.assertEqual(tab.preview_data, {})

if __name__ == "__main__":
    unittest.main()
