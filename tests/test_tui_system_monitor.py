import unittest
import asyncio
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from shared.tui_system_monitor import SystemMonitorTab
from textual.widgets import DataTable, ProgressBar


class MonitorTestApp(App[None]):
    def compose(self) -> ComposeResult:
        yield SystemMonitorTab()


class TestSystemMonitorTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = MonitorTestApp()

    @patch("shared.tui_system_monitor.psutil")
    async def test_update_stats(self, mock_psutil):
        # Setup mocks
        mock_psutil.cpu_percent.return_value = 50.0

        mem = MagicMock()
        mem.percent = 60.0
        mem.used = 6 * 1024 * 1024 * 1024  # 6GB
        mem.total = 10 * 1024 * 1024 * 1024  # 10GB
        mock_psutil.virtual_memory.return_value = mem

        disk = MagicMock()
        disk.percent = 70.0
        mock_psutil.disk_usage.return_value = disk

        # Mock process_iter
        p1 = MagicMock()
        p1.info = {'pid': 1, 'name': 'init', 'username': 'root', 'cpu_percent': 0.1, 'memory_percent': 0.1}
        p1.cpu_percent.return_value = 0.1

        p2 = MagicMock()
        p2.info = {'pid': 100, 'name': 'python', 'username': 'user', 'cpu_percent': 10.0, 'memory_percent': 5.0}
        p2.cpu_percent.return_value = 10.0

        mock_psutil.process_iter.return_value = [p1, p2]

        try:
            async with self.app.run_test() as pilot:
                tab = self.app.query_one(SystemMonitorTab)

                # Force update to ensure mocks are used
                tab.update_stats()

                # Check CPU
                cpu_bar = tab.query_one("#cpu-progress", ProgressBar)
                self.assertEqual(cpu_bar.progress, 50.0)

                # Check Memory
                mem_bar = tab.query_one("#mem-progress", ProgressBar)
                self.assertEqual(mem_bar.progress, 60.0)

                # Check Disk
                disk_bar = tab.query_one("#disk-progress", ProgressBar)
                self.assertEqual(disk_bar.progress, 70.0)

                # Check Process Table
                table = tab.query_one("#proc-table", DataTable)
                self.assertEqual(table.row_count, 2)

                # Verify sorting (python should be first due to higher CPU)
                row1 = table.get_row_at(0)
                self.assertEqual(row1[0], "100")  # PID
                self.assertEqual(row1[1], "python")

                await pilot.pause(0.1)
        except asyncio.CancelledError:
            pass
