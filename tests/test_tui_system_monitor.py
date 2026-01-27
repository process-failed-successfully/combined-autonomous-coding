import unittest
from unittest.mock import MagicMock, patch
from textual.app import App
from shared.tui_system_monitor import SystemMonitorTab

class TestApp(App):
    def compose(self):
        yield SystemMonitorTab()

class TestSystemMonitorTab(unittest.IsolatedAsyncioTestCase):
    async def test_update_stats(self):
        # Mock psutil
        with patch('shared.tui_system_monitor.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value.percent = 60.0
            mock_psutil.disk_usage.return_value.percent = 70.0

            # Mock process
            mock_proc = MagicMock()
            mock_proc.pid = 1234
            mock_proc.cpu_percent.return_value = 10.0
            mock_proc.name.return_value = 'python'
            mock_proc.username.return_value = 'user'
            mock_proc.memory_percent.return_value = 5.0

            # Context manager for oneshot
            mock_proc.oneshot.return_value.__enter__.return_value = mock_proc

            mock_psutil.process_iter.return_value = [mock_proc]

            app = TestApp()
            async with app.run_test() as pilot:
                tab = app.query_one(SystemMonitorTab)

                # First update
                tab.update_stats()

                # Verify cache
                self.assertIn(1234, tab.process_cache)

                # Check widgets
                self.assertEqual(str(tab.query_one("#cpu-digits").value), "50.0")

                # Check table
                table = tab.query_one("#process-table")
                self.assertEqual(table.row_count, 1)
                self.assertEqual(str(table.get_cell_at((0, 0))), "1234")
                self.assertEqual(str(table.get_cell_at((0, 1))), "python")

    async def test_pause_resume(self):
        app = TestApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SystemMonitorTab)
            btn = tab.query_one("#btn-pause-monitor")

            self.assertFalse(tab.paused)

            # Click button
            await pilot.click("#btn-pause-monitor")
            self.assertTrue(tab.paused)
            self.assertEqual(str(btn.label), "Resume")

            # Click again
            await pilot.click("#btn-pause-monitor")
            self.assertFalse(tab.paused)
            self.assertEqual(str(btn.label), "Pause")
