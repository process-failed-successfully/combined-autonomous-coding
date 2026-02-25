import unittest
from unittest.mock import MagicMock, patch
from shared.process_explorer import ProcessExplorerManager

class TestProcessExplorer(unittest.TestCase):
    def setUp(self):
        self.manager = ProcessExplorerManager()

    @patch('shared.process_explorer.psutil.process_iter')
    def test_list_processes(self, mock_iter):
        # Mock processes
        p1 = MagicMock()
        p1.info = {'pid': 1, 'name': 'init', 'username': 'root', 'cpu_percent': 0.1, 'memory_percent': 0.1, 'status': 'sleeping', 'cmdline': ['init']}

        p2 = MagicMock()
        p2.info = {'pid': 100, 'name': 'python', 'username': 'user', 'cpu_percent': 5.0, 'memory_percent': 1.0, 'status': 'running', 'cmdline': ['python', 'script.py']}

        mock_iter.return_value = [p1, p2]

        # Test listing
        procs = self.manager.list_processes(sort_by="pid")
        self.assertEqual(len(procs), 2)
        self.assertEqual(procs[0]['name'], 'init')
        self.assertEqual(procs[1]['name'], 'python')

        # Test filtering
        procs = self.manager.list_processes(filter_text="python")
        self.assertEqual(len(procs), 1)
        self.assertEqual(procs[0]['name'], 'python')

    @patch('shared.process_explorer.psutil.Process')
    def test_get_process_details(self, mock_process_cls):
        mock_proc = MagicMock()
        mock_proc.as_dict.return_value = {
            'pid': 123, 'name': 'test', 'username': 'user', 'status': 'running'
        }
        mock_proc.environ.return_value = {'PATH': '/bin'}

        # Mock open_files
        f = MagicMock()
        f.path = '/tmp/file'
        mock_proc.open_files.return_value = [f]

        # Mock connections
        c = MagicMock()
        c.laddr.ip = '127.0.0.1'
        c.laddr.port = 8080
        c.raddr = None
        c.type = 'TCP'
        c.status = 'LISTEN'
        mock_proc.connections.return_value = [c]

        mock_process_cls.return_value = mock_proc

        details = self.manager.get_process_details(123)
        self.assertEqual(details['pid'], 123)
        self.assertEqual(details['environ'], {'PATH': '/bin'})
        self.assertEqual(details['open_files'], ['/tmp/file'])
        self.assertTrue('TCP 127.0.0.1:8080 -> ? (LISTEN)' in details['connections'])

    @patch('shared.process_explorer.psutil.Process')
    def test_actions(self, mock_process_cls):
        mock_proc = MagicMock()
        mock_process_cls.return_value = mock_proc

        # Kill
        self.assertTrue(self.manager.kill_process(123))
        mock_proc.terminate.assert_called_once()

        # Force Kill
        self.assertTrue(self.manager.kill_process(123, force=True))
        mock_proc.kill.assert_called_once()

        # Suspend
        self.assertTrue(self.manager.suspend_process(123))
        mock_proc.suspend.assert_called_once()

        # Resume
        self.assertTrue(self.manager.resume_process(123))
        mock_proc.resume.assert_called_once()

if __name__ == '__main__':
    unittest.main()
