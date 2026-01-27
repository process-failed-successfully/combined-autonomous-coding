import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Label, ProgressBar, Sparkline, DataTable
from shared.tui_system_monitor import SystemMonitorTab

class SystemMonitorTestApp(App[None]):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield SystemMonitorTab(self.project_dir)

class TestSystemMonitorTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = SystemMonitorTestApp(self.project_dir)

    @patch("shared.tui_system_monitor.psutil")
    async def test_update_stats(self, mock_psutil):
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 50.0

        mock_mem = MagicMock()
        mock_mem.percent = 60.0
        mock_mem.used = 8 * (1024**3)
        mock_mem.total = 16 * (1024**3)
        mock_psutil.virtual_memory.return_value = mock_mem

        mock_disk = MagicMock()
        mock_disk.percent = 70.0
        mock_disk.free = 100 * (1024**3)
        mock_psutil.disk_usage.return_value = mock_disk

        # Mock processes
        # Process 1
        mock_proc1 = MagicMock()
        mock_proc1.info = {'pid': 1001}
        mock_proc1.cpu_percent.return_value = 10.0
        mock_proc1.memory_percent.return_value = 5.0
        mock_proc1.name.return_value = 'python'
        # Context manager support for oneshot()
        mock_proc1.oneshot.return_value.__enter__.return_value = mock_proc1

        # Process 2
        mock_proc2 = MagicMock()
        mock_proc2.info = {'pid': 1002}
        mock_proc2.cpu_percent.return_value = 20.0
        mock_proc2.memory_percent.return_value = 8.0
        mock_proc2.name.return_value = 'node'
        mock_proc2.oneshot.return_value.__enter__.return_value = mock_proc2

        mock_psutil.process_iter.return_value = [mock_proc1, mock_proc2]

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(SystemMonitorTab)

            # Wait for on_mount to trigger initial update
            await pilot.pause(0.2) # Small pause for async update

            # Check CPU Gauge
            cpu_pb = tab.query_one("#pb-cpu", ProgressBar)
            self.assertEqual(cpu_pb.progress, 50.0)

            cpu_lbl = tab.query_one("#lbl-cpu-val", Label)
            self.assertEqual(str(cpu_lbl.render()), "50.0%")

            # Check Memory Gauge
            mem_pb = tab.query_one("#pb-mem", ProgressBar)
            self.assertEqual(mem_pb.progress, 60.0)

            # Check Disk Gauge
            disk_pb = tab.query_one("#pb-disk", ProgressBar)
            self.assertEqual(disk_pb.progress, 70.0)

            # Check Sparklines
            cpu_spark = tab.query_one("#spark-cpu", Sparkline)
            self.assertEqual(cpu_spark.data[-1], 50.0)

            # Check Process Table
            table = tab.query_one("#proc-table", DataTable)
            self.assertEqual(len(table.rows), 2)

            # Verify row content (sorted by CPU desc)
            # Row 0 should be 'node' (20.0%)
            # Columns: PID, Name, CPU %, Memory %
            pid_cell = table.get_cell_at((0, 0))
            name_cell = table.get_cell_at((0, 1))
            self.assertEqual(str(pid_cell), "1002")
            self.assertEqual(str(name_cell), "node")

if __name__ == "__main__":
    unittest.main()
