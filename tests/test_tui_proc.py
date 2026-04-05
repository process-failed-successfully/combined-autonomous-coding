import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog
from shared.tui_proc import ProcLabTab

class ProcLabApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ProcLabTab(self.project_dir)

class TestProcLabTab(unittest.IsolatedAsyncioTestCase):
    @patch("shared.tui_proc.ProcLabManager")
    async def test_mount_and_refresh(self, MockManager):
        # Setup mock manager
        manager = MockManager.return_value
        manager.process_defs = {"web": "echo web", "worker": "echo worker"}
        manager.processes = {}
        manager.load_config = MagicMock()

        app = ProcLabApp(Path("."))
        async with app.run_test() as pilot:
            tab = app.query_one(ProcLabTab)
            table = tab.query_one("#proc-table", DataTable)

            # Check table content
            self.assertEqual(len(table.rows), 2)
            self.assertIn("web", table.rows)
            self.assertIn("worker", table.rows)

            # Check initial buttons state
            self.assertTrue(tab.query_one("#btn-proc-start", Button).disabled)
            self.assertTrue(tab.query_one("#btn-proc-stop", Button).disabled)

    @patch("shared.tui_proc.ProcLabManager")
    async def test_selection_and_actions(self, MockManager):
        manager = MockManager.return_value
        manager.process_defs = {"web": "echo web"}
        manager.processes = {}
        manager.load_config = MagicMock()
        manager.start_process = AsyncMock()
        manager.stop_process = AsyncMock()

        app = ProcLabApp(Path("."))
        async with app.run_test() as pilot:
            tab = app.query_one(ProcLabTab)
            table = tab.query_one("#proc-table", DataTable)

            # Select 'web'
            # Simulate selection event manually
            mock_event = MagicMock()
            mock_event.row_key.value = "web"
            tab.on_process_selected(mock_event)

            # Check buttons (web is stopped)
            self.assertFalse(tab.query_one("#btn-proc-start", Button).disabled)
            self.assertTrue(tab.query_one("#btn-proc-stop", Button).disabled)

            # Click Start
            app.query_one("#btn-proc-start").press()
        await pilot.pause()

            # Verify start_process called
            manager.start_process.assert_awaited_with("web", on_output=tab.on_process_output)

            # Simulate process started (mock state change)
            mock_proc = MagicMock()
            mock_proc.returncode = None # Running
            mock_proc.pid = 123
            manager.processes["web"] = mock_proc

            # Refresh table
            tab.refresh_table()
            tab._update_buttons("web")

            # Check buttons (web is running)
            self.assertTrue(tab.query_one("#btn-proc-start", Button).disabled)
            self.assertFalse(tab.query_one("#btn-proc-stop", Button).disabled)

            # Click Stop
            app.query_one("#btn-proc-stop").press()
        await pilot.pause()
            manager.stop_process.assert_awaited_with("web")

    @patch("shared.tui_proc.ProcLabManager")
    async def test_logs(self, MockManager):
        manager = MockManager.return_value
        manager.process_defs = {"web": "echo web"}
        manager.processes = {}

        app = ProcLabApp(Path("."))
        async with app.run_test() as pilot:
            tab = app.query_one(ProcLabTab)

            # Simulate output
            tab.selected_process = "web"
            tab.on_process_output("web", "Starting web server...")

            # Check log
            log = tab.query_one("#proc-log", RichLog)

            self.assertIn("web", tab.output_buffers)
            self.assertEqual(tab.output_buffers["web"][-1], "Starting web server...")

if __name__ == "__main__":
    unittest.main()
