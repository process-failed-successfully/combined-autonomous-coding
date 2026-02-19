import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button
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

    @patch("shared.tui_proc.ProcLabManager")
    async def test_load_processes(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.parse_procfile.return_value = {"web": "python server.py", "worker": "python worker.py"}
        mock_instance.processes = {}
        mock_instance.stop_all = AsyncMock()

        async with self.app.run_test():
            tab = self.app.query_one(ProcLabTab)
            table = tab.query_one("#proc-table", DataTable)

            # Should have loaded 2 rows
            self.assertEqual(table.row_count, 2)
            self.assertEqual(tab.proc_map["web"], "python server.py")

    @patch("shared.tui_proc.ProcLabManager")
    async def test_start_process(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.parse_procfile.return_value = {"web": "cmd"}
        mock_instance.processes = {}
        mock_instance.start_process = AsyncMock(return_value=True)
        mock_instance.stop_all = AsyncMock()

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ProcLabTab)

            # Select process
            tab.selected_process = "web"
            tab.update_buttons()  # Update state

            btn_start = tab.query_one("#btn-proc-start", Button)
            self.assertFalse(btn_start.disabled)

            await pilot.click("#btn-proc-start")

            mock_instance.start_process.assert_called_once()
            args, _ = mock_instance.start_process.call_args
            self.assertEqual(args[0], "web")
            self.assertEqual(args[1], "cmd")

    @patch("shared.tui_proc.ProcLabManager")
    async def test_stop_process(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.parse_procfile.return_value = {"web": "cmd"}
        # Simulate running process
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_instance.processes = {"web": mock_proc}

        mock_instance.stop_process = AsyncMock(return_value=True)
        mock_instance.stop_all = AsyncMock()

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(ProcLabTab)

            # Select process
            tab.selected_process = "web"
            tab.update_buttons()

            btn_stop = tab.query_one("#btn-proc-stop", Button)
            self.assertFalse(btn_stop.disabled)

            await pilot.click("#btn-proc-stop")

            mock_instance.stop_process.assert_called_with("web")


if __name__ == "__main__":
    unittest.main()
