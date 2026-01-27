import unittest
from unittest.mock import MagicMock, patch
from shared.tui_system_monitor import SystemMonitorTab
from pathlib import Path

class TestSystemMonitorTab(unittest.TestCase):
    def test_update_stats(self):
        # Mock psutil
        with patch('shared.tui_system_monitor.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = MagicMock(percent=60.0, used=1000, total=2000)
            mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)

            # Mock process_iter
            # process_iter yields objects that have an .info attribute if we access it that way,
            # or we iterate over it. The code uses process_iter(['...']) loop.
            p1 = MagicMock()
            p1.info = {'pid': 1, 'name': 'init', 'username': 'root', 'cpu_percent': 0.1, 'memory_percent': 0.1}

            p2 = MagicMock()
            p2.info = {'pid': 2, 'name': 'python', 'username': 'user', 'cpu_percent': 10.0, 'memory_percent': 5.0}

            mock_psutil.process_iter.return_value = [p1, p2]

            # Initialize Tab
            tab = SystemMonitorTab(Path("."))

            # Mock query_one to return mock widgets
            mock_cpu_label = MagicMock()
            mock_mem_label = MagicMock()
            mock_disk_label = MagicMock()
            mock_table = MagicMock()

            def query_side_effect(selector, type=None):
                if selector == "#lbl-cpu": return mock_cpu_label
                if selector == "#lbl-memory": return mock_mem_label
                if selector == "#lbl-disk": return mock_disk_label
                if selector == "#proc-table": return mock_table
                return MagicMock()

            tab.query_one = MagicMock(side_effect=query_side_effect)

            # Call update_stats
            tab.update_stats()

            # Verify psutil calls
            mock_psutil.cpu_percent.assert_called()

            # Verify UI updates
            mock_cpu_label.update.assert_called()
            # Check content contains percentage
            self.assertIn("50.0%", str(mock_cpu_label.update.call_args))

            mock_mem_label.update.assert_called()
            mock_disk_label.update.assert_called()

            # Verify table update
            mock_table.clear.assert_called()
            # We expect 2 add_row calls
            self.assertEqual(mock_table.add_row.call_count, 2)

            # Check if sorting worked (python with 10.0% cpu should be first, but add_row call order matters)
            # Actually we can check the call args of the first add_row
            first_call_args = mock_table.add_row.call_args_list[0]
            # args: (pid, name, user, cpu, mem)
            # p2 is python, pid 2
            self.assertEqual(first_call_args[0][0], '2')
            self.assertEqual(first_call_args[0][1], 'python')

    def test_bytes_to_human(self):
        tab = SystemMonitorTab(Path("."))
        self.assertEqual(tab.bytes_to_human(1024), "1.0K")
        self.assertEqual(tab.bytes_to_human(1024*1024), "1.0M")
        self.assertEqual(tab.bytes_to_human(500), "500B")

if __name__ == '__main__':
    unittest.main()
