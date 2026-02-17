import unittest
from unittest.mock import MagicMock, patch
import signal
from shared.monitor_lab import MonitorLabManager


class TestMonitorLabManager(unittest.TestCase):

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_stats(self, mock_disk, mock_mem, mock_cpu):
        mock_cpu.return_value = 15.5

        mock_mem_obj = MagicMock()
        mock_mem_obj.percent = 45.0
        mock_mem_obj.used = 1024
        mock_mem_obj.total = 4096
        mock_mem_obj.available = 3072
        mock_mem.return_value = mock_mem_obj

        mock_disk_obj = MagicMock()
        mock_disk_obj.percent = 60.0
        mock_disk_obj.used = 100
        mock_disk_obj.total = 200
        mock_disk_obj.free = 100
        mock_disk.return_value = mock_disk_obj

        manager = MonitorLabManager()
        stats = manager.get_system_stats()

        self.assertEqual(stats['cpu'], 15.5)
        self.assertEqual(stats['memory']['percent'], 45.0)
        self.assertEqual(stats['disk']['percent'], 60.0)

    @patch('time.sleep')
    @patch('psutil.process_iter')
    def test_get_processes(self, mock_process_iter, mock_sleep):
        # Mock Process objects
        p1 = MagicMock()
        p1.as_dict.return_value = {'pid': 1, 'name': 'init', 'username': 'root', 'cpu_percent': 0.1, 'memory_percent': 0.1, 'status': 'sleeping'}

        p2 = MagicMock()
        p2.as_dict.return_value = {'pid': 100, 'name': 'python', 'username': 'user', 'cpu_percent': 10.5, 'memory_percent': 5.0, 'status': 'running'}

        # process_iter is called once
        mock_process_iter.return_value = [p1, p2]

        manager = MonitorLabManager()

        # Test default sort (cpu desc)
        procs = manager.get_processes()

        # Verify cpu_percent called for warmup
        p1.cpu_percent.assert_called()
        p2.cpu_percent.assert_called()

        # Verify sleep called
        mock_sleep.assert_called_with(0.1)

        # Verify as_dict called
        p1.as_dict.assert_called()
        p2.as_dict.assert_called()

        self.assertEqual(len(procs), 2)
        self.assertEqual(procs[0]['name'], 'python')  # Higher CPU

        # Test filtering
        # We need to reset mocks if we want to run again cleanly, or just check result
        # process_iter is called again
        mock_process_iter.return_value = [p1, p2]
        procs = manager.get_processes(filter_pattern="py")
        self.assertEqual(len(procs), 1)
        self.assertEqual(procs[0]['name'], 'python')

    @patch('psutil.Process')
    def test_kill_process(self, mock_process_cls):
        mock_proc_instance = MagicMock()
        mock_process_cls.return_value = mock_proc_instance

        manager = MonitorLabManager()
        result = manager.kill_process(123)

        self.assertTrue(result)
        mock_process_cls.assert_called_with(123)
        mock_proc_instance.send_signal.assert_called_with(signal.SIGTERM)

    @patch('psutil.Process')
    def test_kill_process_not_found(self, mock_process_cls):
        import psutil
        mock_process_cls.side_effect = psutil.NoSuchProcess(123)

        manager = MonitorLabManager()
        result = manager.kill_process(123)

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
