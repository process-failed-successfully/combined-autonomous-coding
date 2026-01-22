import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import DataTable, Input, Select, Button  # noqa: E402
from shared.tui import AgentTUI, TasksTab  # noqa: E402
from shared.task_manager import Task  # noqa: E402


class TestTUITasks(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock dependencies
        self.patcher_db = patch("shared.tui.init_db")
        self.mock_init_db = self.patcher_db.start()

        self.patcher_km = patch("shared.tui.KnowledgeManager")
        self.mock_km = self.patcher_km.start()

        self.patcher_ask = patch("shared.tui.run_ask_logic", new_callable=AsyncMock)
        self.mock_ask = self.patcher_ask.start()

        self.patcher_tm = patch("shared.tui.TaskManager")
        self.mock_tm_class = self.patcher_tm.start()
        self.mock_tm = self.mock_tm_class.return_value

    def tearDown(self) -> None:
        self.patcher_db.stop()
        self.patcher_km.stop()
        self.patcher_ask.stop()
        self.patcher_tm.stop()
        shutil.rmtree(self.test_dir)

    async def test_tasks_tab_structure(self) -> None:
        """Test that the Tasks tab has the correct widgets."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Check if tab exists
            self.assertTrue(app.query_one("#tab-tasks"))

            # Switch to tasks tab
            app.query_one("TabbedContent").active = "tab-tasks"  # type: ignore
            await pilot.pause()

            tasks_tab = app.query_one(TasksTab)
            self.assertIsNotNone(tasks_tab)

            self.assertIsInstance(tasks_tab.query_one("#tasks-table"), DataTable)
            self.assertIsInstance(tasks_tab.query_one("#btn-tasks-refresh"), Button)
            self.assertIsInstance(tasks_tab.query_one("#select-task-source"), Select)
            self.assertIsInstance(tasks_tab.query_one("#input-task-filter"), Input)

    async def test_tasks_load(self) -> None:
        """Test that tasks are loaded into the table."""
        mock_tasks = [
            Task(id="1", source="github", title="Task 1", status="Open"),
            Task(id="2", source="todo", title="Task 2", status="Open")
        ]
        self.mock_tm.fetch_all_tasks.return_value = mock_tasks

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("TabbedContent").active = "tab-tasks"  # type: ignore
            await pilot.pause()

            tasks_tab = app.query_one(TasksTab)
            table = tasks_tab.query_one("#tasks-table", DataTable)

            self.assertEqual(table.row_count, 2)
            self.mock_tm.fetch_all_tasks.assert_called()

    async def test_tasks_refresh(self) -> None:
        """Test the refresh button."""
        self.mock_tm.fetch_all_tasks.return_value = []

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("TabbedContent").active = "tab-tasks"  # type: ignore
            await pilot.pause()

            initial_count = self.mock_tm.fetch_all_tasks.call_count

            await pilot.click("#btn-tasks-refresh")
            await pilot.pause()

            self.assertGreater(self.mock_tm.fetch_all_tasks.call_count, initial_count)

    async def test_tasks_filter(self) -> None:
        """Test filtering tasks locally."""
        mock_tasks = [
            Task(id="1", source="github", title="Alpha", status="Open"),
            Task(id="2", source="todo", title="Beta", status="Open")
        ]
        self.mock_tm.fetch_all_tasks.return_value = mock_tasks

        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("TabbedContent").active = "tab-tasks"  # type: ignore
            await pilot.pause()

            tasks_tab = app.query_one(TasksTab)
            table = tasks_tab.query_one("#tasks-table", DataTable)
            self.assertEqual(table.row_count, 2)

            # Filter by text
            await pilot.click("#input-task-filter")
            await pilot.press("A", "l", "p")
            await pilot.pause()

            # Should filter to 1
            if table.row_count == 2:
                 input_widget = tasks_tab.query_one("#input-task-filter", Input)
                 input_widget.value = "Alp"
                 await pilot.pause()

            self.assertLess(table.row_count, 2)

if __name__ == "__main__":
    unittest.main()
