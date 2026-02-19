import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog
from shared.tui_proc import ProcLabTab

class ProcTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield ProcLabTab(self.project_dir)

class TestProcLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = ProcTestApp(self.project_dir)

        # Patch the manager globally for this test class instance
        self.patcher = patch("shared.tui_proc.ProcLabManager")
        self.MockManager = self.patcher.start()

        # Configure the mock instance
        self.mock_instance = self.MockManager.return_value
        # Important: stop_all is awaited in on_unmount, so it MUST be an AsyncMock
        self.mock_instance.stop_all = AsyncMock(return_value=True)
        self.mock_instance.start_process = AsyncMock(return_value=True)
        self.mock_instance.stop_process = AsyncMock(return_value=True)

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_load_processes(self):
        self.mock_instance.parse_procfile.return_value = {"web": "python server.py", "worker": "python worker.py"}
        self.mock_instance.processes = {}

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ProcLabTab)
            table = tab.query_one("#proc-table", DataTable)

            # Should have loaded 2 rows
            self.assertEqual(table.row_count, 2)
            self.assertEqual(tab.proc_map["web"], "python server.py")

    async def test_start_process(self):
        self.mock_instance.parse_procfile.return_value = {"web": "cmd"}
        self.mock_instance.processes = {}
        # start_process is already AsyncMock from setUp

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ProcLabTab)

            # Select process
            tab.selected_process = "web"
            tab.update_buttons() # Update state

            btn_start = tab.query_one("#btn-proc-start", Button)
            self.assertFalse(btn_start.disabled)

            await pilot.click("#btn-proc-start")

            self.mock_instance.start_process.assert_called_once()
            args, _ = self.mock_instance.start_process.call_args
            self.assertEqual(args[0], "web")
            self.assertEqual(args[1], "cmd")

    async def test_stop_process(self):
        self.mock_instance.parse_procfile.return_value = {"web": "cmd"}
        # Simulate running process
        mock_proc = MagicMock()
        mock_proc.returncode = None
        self.mock_instance.processes = {"web": mock_proc}

        # stop_process is already AsyncMock from setUp

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ProcLabTab)

            # Select process
            tab.selected_process = "web"
            tab.update_buttons()

            btn_stop = tab.query_one("#btn-proc-stop", Button)
            self.assertFalse(btn_stop.disabled)

            await pilot.click("#btn-proc-stop")

            self.mock_instance.stop_process.assert_called_with("web")

if __name__ == "__main__":
    unittest.main()
