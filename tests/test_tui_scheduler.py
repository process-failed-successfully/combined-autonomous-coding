import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog
from shared.tui_scheduler import SchedulerTab, TUIScheduler
from shared.scheduler import Task

class SchedulerTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield SchedulerTab(self.project_dir)

class TestTUIScheduler(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.log_widget = MagicMock(spec=RichLog)
        self.scheduler = TUIScheduler(self.project_dir, self.log_widget)

    @patch("subprocess.run")
    def test_run_task_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Success output", stderr="")
        task = Task(name="Test Task", command="echo test", interval=60)

        # Mock call_from_thread to execute immediately
        def side_effect(callback, *args):
            callback(*args)
        self.log_widget.app.call_from_thread.side_effect = side_effect

        self.scheduler.run_task(task)

        mock_run.assert_called_once()
        self.log_widget.write.assert_any_call(f"\n[bold blue][Scheduler] Running: {task.name}[/bold blue]")
        # Check that success message was written
        calls = [args[0] for args, _ in self.log_widget.write.call_args_list]
        self.assertTrue(any("completed" in c for c in calls))

    @patch("subprocess.run")
    def test_run_task_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error output")
        task = Task(name="Fail Task", command="exit 1", interval=60)

        # Mock call_from_thread to execute immediately
        def side_effect(callback, *args):
            callback(*args)
        self.log_widget.app.call_from_thread.side_effect = side_effect

        self.scheduler.run_task(task)

        calls = [args[0] for args, _ in self.log_widget.write.call_args_list]
        self.assertTrue(any("failed" in c for c in calls))
        self.assertTrue(any("Error output" in c for c in calls))

class TestSchedulerTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = SchedulerTestApp(self.project_dir)

    @patch("shared.tui_scheduler.TUIScheduler.load_config")
    async def test_initialization(self, mock_load):
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(SchedulerTab)
            self.assertIsNotNone(tab.scheduler)
            mock_load.assert_called_once()

            # Check table columns
            table = tab.query_one("#sched-table", DataTable)
            self.assertEqual(len(table.columns), 5)

    @patch("shared.tui_scheduler.TUIScheduler.load_config")
    async def test_start_stop(self, mock_load):
        async with self.app.run_test(size=(80, 24)) as pilot:
            tab = self.app.query_one(SchedulerTab)

            # Start
            pilot.app.query_one("#btn-sched-start").press()
            await pilot.pause()
            self.assertTrue(tab.scheduler_active)
            self.assertIsNotNone(tab.timer)
            self.assertTrue(tab.query_one("#btn-sched-start").disabled)
            self.assertFalse(tab.query_one("#btn-sched-stop").disabled)

            # Stop
            pilot.app.query_one("#btn-sched-stop").press()
            await pilot.pause()
            self.assertFalse(tab.scheduler_active)
            self.assertIsNone(tab.timer)

if __name__ == "__main__":
    unittest.main()
