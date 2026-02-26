import unittest
from unittest.mock import MagicMock, patch
from shared.process_explorer import ProcessExplorerManager

class TestProcessExplorer(unittest.TestCase):
    def setUp(self):
        self.manager = ProcessExplorerManager()

    @patch('shared.process_explorer.psutil.process_iter')
    def test_list_processes(self, mock_process_iter):
        # Mock process objects
        proc1 = MagicMock()
        proc1.info = {'pid': 1, 'name': 'init', 'username': 'root', 'status': 'running', 'cpu_percent': 0.0, 'memory_percent': 0.1, 'cmdline': ['init'], 'create_time': 1000}

        proc2 = MagicMock()
        proc2.info = {'pid': 100, 'name': 'python', 'username': 'user', 'status': 'running', 'cpu_percent': 10.0, 'memory_percent': 1.0, 'cmdline': ['python', 'main.py'], 'create_time': 2000}

        mock_process_iter.return_value = [proc1, proc2]

        # Test list all
        processes = self.manager.list_processes()
        self.assertEqual(len(processes), 2)
        self.assertEqual(processes[0]['name'], 'init')

        # Test filtering
        processes_filtered = self.manager.list_processes(filter_str="python")
        self.assertEqual(len(processes_filtered), 1)
        self.assertEqual(processes_filtered[0]['name'], 'python')

    @patch('shared.process_explorer.psutil.Process')
    def test_get_process_details(self, mock_Process):
        mock_proc = MagicMock()
        mock_proc.pid = 123
        mock_proc.name.return_value = "test_proc"
        mock_proc.status.return_value = "running"
        mock_proc.username.return_value = "test_user"
        mock_proc.cpu_percent.return_value = 5.5
        mock_proc.memory_info.return_value = MagicMock(rss=1024, vms=2048, _asdict=lambda: {'rss': 1024, 'vms': 2048})
        mock_proc.cmdline.return_value = ["test_proc", "--flag"]
        mock_proc.environ.return_value = {"PATH": "/bin"}

        mock_Process.return_value = mock_proc

        details = self.manager.get_process_details(123)
        self.assertEqual(details['pid'], 123)
        self.assertEqual(details['name'], "test_proc")
        self.assertEqual(details['username'], "test_user")
        self.assertEqual(details['cpu_percent'], 5.5)
        self.assertEqual(details['cmdline'], ["test_proc", "--flag"])

    @patch('shared.process_explorer.psutil.Process')
    def test_kill_process(self, mock_Process):
        mock_proc = MagicMock()
        mock_Process.return_value = mock_proc

        # Success
        result = self.manager.kill_process(123)
        self.assertTrue(result)
        mock_proc.terminate.assert_called_once()

        # Force kill
        result = self.manager.kill_process(123, force=True)
        self.assertTrue(result)
        mock_proc.kill.assert_called_once()

    @patch('shared.process_explorer.psutil.Process')
    def test_suspend_resume(self, mock_Process):
        mock_proc = MagicMock()
        mock_Process.return_value = mock_proc

        self.assertTrue(self.manager.suspend_process(123))
        mock_proc.suspend.assert_called_once()

        self.assertTrue(self.manager.resume_process(123))
        mock_proc.resume.assert_called_once()

if __name__ == '__main__':
    unittest.main()
