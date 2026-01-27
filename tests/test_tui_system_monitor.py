import unittest
from unittest.mock import MagicMock, patch
from textual.app import App
from textual.widgets import Digits, DataTable
from shared.tui_system_monitor import SystemMonitorTab

class TestApp(App[None]):
    def compose(self):
        yield SystemMonitorTab()

class TestSystemMonitorTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestApp()

    @patch('shared.tui_system_monitor.psutil')
    async def test_update_stats(self, mock_psutil):
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 50.0

        mock_mem = MagicMock()
        mock_mem.percent = 60.0
        mock_mem.used = 6000
        mock_mem.total = 10000
        mock_psutil.virtual_memory.return_value = mock_mem

        mock_disk = MagicMock()
        mock_disk.percent = 70.0
        mock_disk.free = 3000
        mock_disk.total = 10000
        mock_psutil.disk_usage.return_value = mock_disk

        mock_net = MagicMock()
        mock_net.bytes_sent = 1000
        mock_net.bytes_recv = 2000
        mock_psutil.net_io_counters.return_value = mock_net

        # Mock processes
        p1 = MagicMock()
        p1.pid = 123
        p1.name.return_value = "python"
        p1.username.return_value = "user"
        p1.cpu_percent.return_value = 10.0
        p1.memory_percent.return_value = 5.0
        p1.status.return_value = "running"
        p1.oneshot.return_value.__enter__.return_value = p1

        mock_psutil.process_iter.return_value = [p1]

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(SystemMonitorTab)

            # Trigger update manually
            tab.update_stats()

            # Check CPU
            cpu_digits = tab.query_one("#cpu-digits", Digits)
            self.assertEqual(str(cpu_digits.value), "50.0%")

            # Check Memory
            mem_digits = tab.query_one("#mem-digits", Digits)
            self.assertEqual(str(mem_digits.value), "60.0%")

            # Check Process Table
            table = tab.query_one("#proc-table", DataTable)
            self.assertEqual(table.row_count, 1)
            row = table.get_row_at(0)
            self.assertEqual(row[0], "123") # PID
            self.assertEqual(row[1], "python") # Name
