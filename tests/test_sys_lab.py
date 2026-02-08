import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
from pathlib import Path
import os

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.sys_lab import SysLabManager

class TestSysLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = SysLabManager()

    @patch('shared.sys_lab.platform.uname')
    @patch('shared.sys_lab.psutil')
    def test_get_system_info(self, mock_psutil, mock_uname):
        # Mock platform.uname
        mock_uname.return_value = MagicMock(
            system='Linux',
            release='5.15.0',
            version='#1 SMP',
            machine='x86_64',
            processor='x86_64'
        )

        # Mock psutil
        mock_psutil.cpu_count.side_effect = [4, 8] # physical, logical
        mock_psutil.cpu_percent.return_value = 15.5
        mock_psutil.cpu_freq.return_value = MagicMock(current=2400, min=800, max=4000)

        mock_mem = MagicMock()
        mock_mem.total = 16000000000
        mock_mem.available = 8000000000
        mock_mem.used = 8000000000
        mock_mem.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_mem

        mock_disk = MagicMock()
        mock_disk.total = 500000000000
        mock_disk.used = 250000000000
        mock_disk.free = 250000000000
        mock_disk.percent = 50.0
        mock_psutil.disk_usage.return_value = mock_disk

        info = self.manager.get_system_info()

        self.assertEqual(info['system']['os'], "Linux 5.15.0")
        self.assertEqual(info['cpu']['physical_cores'], 4)
        self.assertEqual(info['cpu']['logical_cores'], 8)
        self.assertEqual(info['memory']['percent'], 50.0)
        self.assertEqual(info['disk']['root_percent'], 50.0)

    @patch('shared.sys_lab.psutil.process_iter')
    def test_list_processes(self, mock_process_iter):
        # Mock processes
        p1 = MagicMock()
        p1.info = {'pid': 1, 'name': 'init', 'username': 'root', 'cpu_percent': 0.1, 'memory_percent': 0.1, 'status': 'sleeping', 'cmdline': ['/sbin/init']}

        p2 = MagicMock()
        p2.info = {'pid': 100, 'name': 'python', 'username': 'user', 'cpu_percent': 50.0, 'memory_percent': 2.0, 'status': 'running', 'cmdline': ['python', 'script.py']}

        p3 = MagicMock()
        p3.info = {'pid': 200, 'name': 'chrome', 'username': 'user', 'cpu_percent': 10.0, 'memory_percent': 5.0, 'status': 'running', 'cmdline': ['chrome']}

        mock_process_iter.return_value = [p1, p2, p3]

        # Test sort by cpu (default)
        procs = self.manager.list_processes()
        self.assertEqual(len(procs), 3)
        self.assertEqual(procs[0]['pid'], 100) # Highest CPU

        # Test filter
        procs = self.manager.list_processes(filter_name="python")
        self.assertEqual(len(procs), 1)
        self.assertEqual(procs[0]['name'], 'python')

        # Test user
        procs = self.manager.list_processes(user="root")
        self.assertEqual(len(procs), 1)
        self.assertEqual(procs[0]['username'], 'root')

    @patch('shared.sys_lab.psutil.Process')
    def test_kill_process_pid(self, mock_process_cls):
        mock_proc = MagicMock()
        mock_process_cls.return_value = mock_proc
        mock_proc.name.return_value = "test_proc"

        result = self.manager.kill_process(pid=1234)

        mock_process_cls.assert_called_with(1234)
        mock_proc.send_signal.assert_called_with(15) # Default SIGTERM
        self.assertTrue(result['success'])

    @patch('shared.sys_lab.psutil.process_iter')
    def test_kill_process_name_multiple(self, mock_process_iter):
        p1 = MagicMock()
        p1.info = {'pid': 100, 'name': 'target'}
        p1.pid = 100

        p2 = MagicMock()
        p2.info = {'pid': 101, 'name': 'target'}
        p2.pid = 101

        mock_process_iter.return_value = [p1, p2]

        # Without force
        result = self.manager.kill_process(name="target")
        self.assertFalse(result['success'])
        self.assertIn("Found 2 processes", result['message'])

        # With force
        result = self.manager.kill_process(name="target", force=True)
        self.assertTrue(result['success'])
        self.assertEqual(len(result['killed']), 2)

    @patch('shared.sys_lab.os.scandir')
    @patch('shared.sys_lab.SysLabManager._get_dir_size')
    def test_analyze_disk_usage(self, mock_get_dir_size, mock_scandir):
        # Mock file entry
        f1 = MagicMock()
        f1.is_file.return_value = True
        f1.is_dir.return_value = False
        f1.name = "large_file.txt"
        f1.path = "/path/large_file.txt"
        f1.stat.return_value.st_size = 1000

        # Mock dir entry
        d1 = MagicMock()
        d1.is_file.return_value = False
        d1.is_dir.return_value = True
        d1.name = "sub_dir"
        d1.path = "/path/sub_dir"

        mock_scandir.return_value.__enter__.return_value = [f1, d1]
        mock_get_dir_size.return_value = 5000

        with patch('pathlib.Path.exists', return_value=True):
            items = self.manager.analyze_disk_usage(Path("/path"))

        self.assertEqual(len(items), 2)
        # Should be sorted by size desc
        self.assertEqual(items[0]['name'], 'sub_dir')
        self.assertEqual(items[0]['size'], 5000)
        self.assertEqual(items[1]['name'], 'large_file.txt')
        self.assertEqual(items[1]['size'], 1000)

    def test_format_bytes(self):
        self.assertEqual(self.manager.format_bytes(1024), "1.00 KB")
        self.assertEqual(self.manager.format_bytes(1024**2), "1.00 MB")
        self.assertEqual(self.manager.format_bytes(500), "500.00 B")

if __name__ == '__main__':
    unittest.main()
