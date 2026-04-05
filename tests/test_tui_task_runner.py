import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from textual.app import App, ComposeResult
from pathlib import Path
from shared.tui_task_runner import TaskRunnerTab
from shared.task_runner_lab import Task

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield TaskRunnerTab(Path("."))

class TestTuiTaskRunner(unittest.IsolatedAsyncioTestCase):
    async def test_mount_and_load(self):
        # Mock manager
        with patch("shared.tui_task_runner.TaskRunnerManager") as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.list_tasks.return_value = [
                Task("npm", "test", "npm test", "package.json", "test"),
                Task("Makefile", "build", "make build", "Makefile", "build")
            ]

            app = TestApp()
            async with app.run_test() as pilot:
                tab = app.query_one(TaskRunnerTab)
                table = tab.query_one("#runner-table")

                # Check table population
                self.assertEqual(len(table.rows), 2)
                self.assertEqual(table.get_cell_at((0, 1)), "test")
                self.assertEqual(table.get_cell_at((1, 1)), "build")

    async def test_run_task(self):
        with patch("shared.tui_task_runner.TaskRunnerManager") as MockManager:
            mock_instance = MockManager.return_value
            mock_task = Task("npm", "test", "npm test", "package.json", "test")
            mock_instance.list_tasks.return_value = [mock_task]
            # run_task is called in a thread, need to ensure it doesn't block or fail
            mock_instance.run_task.return_value = 0

            app = TestApp()
            async with app.run_test() as pilot:
                tab = app.query_one(TaskRunnerTab)

                # Select first row
                # Textual 0.64.0: click on row? or select via API
                table = tab.query_one("#runner-table")
                table.action_select_cursor() # This requires cursor to be set
                # Just simulate selection logic directly
                tab.on_task_selected(MagicMock(row_key=MagicMock(value="0")))

                # Check button enabled
                btn_run = tab.query_one("#btn-runner-run")
                self.assertFalse(btn_run.disabled)

                # Click run
                app.query_one("#btn-runner-run").press()
        await pilot.pause()

                # Verify run_task called
                # It's in a thread, so might take a moment?
                # Actually run_test awaits scheduled tasks?
                # Textual's app.call_from_thread might complicate verification if we don't wait.

                # Since we await pilot.click, and the handler is async and awaits to_thread...
                # It should be done.
                mock_instance.run_task.assert_called()
                args, _ = mock_instance.run_task.call_args
                self.assertEqual(args[0].name, "test")
                self.assertEqual(args[0].script_key, "test")
