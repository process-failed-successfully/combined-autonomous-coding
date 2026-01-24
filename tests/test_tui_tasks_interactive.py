import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.widgets import Input, Button, DataTable
from shared.tui import TasksTab
from shared.task_manager import Task

class TasksTestApp(App):
    CSS = """
    .input-small { width: 20%; }
    .input-large { width: 50%; }
    .btn-auto { width: auto; }
    """
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield TasksTab(self.project_dir)

class TestTUITasksInteractive(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Patch TaskManager
        self.patcher_tm = patch("shared.tui.TaskManager")
        self.mock_tm_cls = self.patcher_tm.start()
        self.mock_tm = self.mock_tm_cls.return_value

        # Setup default mocks
        self.mock_tm.fetch_all_tasks.return_value = []
        self.mock_tm.add_feature.return_value = True
        self.mock_tm.update_feature_status.return_value = True
        self.mock_tm.delete_feature.return_value = True

    def tearDown(self):
        self.patcher_tm.stop()
        shutil.rmtree(self.test_dir)

    async def test_add_feature(self):
        app = TasksTestApp(self.project_dir)
        # Set large screen size
        async with app.run_test(size=(200, 50)) as pilot:
            # Find widgets
            title_input = app.query_one("#task-input-title", Input)
            desc_input = app.query_one("#task-input-desc", Input)
            add_btn = app.query_one("#btn-task-add", Button)

            # Interact
            title_input.value = "New Feature"
            desc_input.value = "Some description"

            await pilot.pause()

            # Try pressing directly if click fails
            try:
                await pilot.click("#btn-task-add")
            except Exception:
                add_btn.press()
                await pilot.pause()

            # Verify
            self.mock_tm.add_feature.assert_called_with("New Feature", "Some description")
            # Should reload tasks
            self.mock_tm.fetch_all_tasks.assert_called()

    async def test_action_buttons(self):
        # Setup mock tasks
        task = Task(id="feat_1", source="feature", title="Test Feature", status="Pending")
        self.mock_tm.fetch_all_tasks.return_value = [task]

        app = TasksTestApp(self.project_dir)
        async with app.run_test(size=(200, 50)) as pilot:
            table = app.query_one("#tasks-table", DataTable)

            # Wait for table to populate
            await pilot.pause()

            # Verify table content
            self.assertEqual(table.row_count, 1)

            # Select row (index 0)
            table.move_cursor(row=0)
            table.action_select_cursor() # This triggers on_row_selected
            await pilot.pause()

            # Verify buttons enabled
            self.assertFalse(app.query_one("#btn-task-done", Button).disabled)
            self.assertFalse(app.query_one("#btn-task-delete", Button).disabled)

            # Click Mark Done
            try:
                await pilot.click("#btn-task-done")
            except Exception:
                app.query_one("#btn-task-done", Button).press()
                await pilot.pause()

            self.mock_tm.update_feature_status.assert_called_with("feat_1", "Done")

            # Click Delete
            try:
                await pilot.click("#btn-task-delete")
            except Exception:
                app.query_one("#btn-task-delete", Button).press()
                await pilot.pause()

            self.mock_tm.delete_feature.assert_called_with("feat_1")

if __name__ == "__main__":
    unittest.main()
