import unittest
from unittest.mock import MagicMock, patch
from shared.port_manager import PortManager
import psutil

class TestPortManager(unittest.TestCase):
    def setUp(self):
        self.manager = PortManager()

    @patch('shared.port_manager.psutil')
    def test_list_listening_ports(self, mock_psutil):
        # Mock connection object
        conn1 = MagicMock()
        conn1.status = "LISTEN"
        conn1.laddr.port = 8000
        conn1.laddr.ip = '127.0.0.1'
        conn1.pid = 1234

        conn2 = MagicMock()
        conn2.status = "ESTABLISHED" # Should be ignored
        conn2.laddr.port = 9000
        conn2.pid = 5678

        mock_psutil.net_connections.return_value = [conn1, conn2]
        mock_psutil.CONN_LISTEN = "LISTEN"

        # Mock process
        mock_process = MagicMock()
        mock_process.name.return_value = "python"
        mock_psutil.Process.return_value = mock_process

        ports = self.manager.list_listening_ports()

        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['port'], 8000)
        self.assertEqual(ports[0]['pid'], 1234)
        self.assertEqual(ports[0]['name'], "python")

    @patch('shared.port_manager.psutil')
    def test_check_port_in_use(self, mock_psutil):
        conn = MagicMock()
        conn.laddr.port = 3000
        conn.laddr.ip = '0.0.0.0'
        conn.pid = 999
        conn.status = "LISTEN"

        mock_psutil.net_connections.return_value = [conn]

        mock_process = MagicMock()
        mock_process.name.return_value = "node"
        mock_psutil.Process.return_value = mock_process

        info = self.manager.check_port(3000)

        self.assertIsNotNone(info)
        self.assertEqual(info['port'], 3000)
        self.assertEqual(info['name'], "node")

    @patch('shared.port_manager.psutil')
    def test_check_port_free(self, mock_psutil):
        mock_psutil.net_connections.return_value = []
        info = self.manager.check_port(8080)
        self.assertIsNone(info)

    @patch('shared.port_manager.psutil')
    def test_kill_process_on_port(self, mock_psutil):
        # Setup check_port to return a process
        conn = MagicMock()
        conn.laddr.port = 5000
        conn.pid = 100
        mock_psutil.net_connections.return_value = [conn]

        mock_process = MagicMock()
        mock_psutil.Process.return_value = mock_process

        result = self.manager.kill_process_on_port(5000)

        self.assertTrue(result)
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    @patch('shared.port_manager.psutil')
    def test_wait_for_port_free(self, mock_psutil):
        # First call returns used, second returns empty (free)
        conn = MagicMock()
        conn.laddr.port = 4000
        conn.pid = 55
        conn.status = "LISTEN"
        mock_psutil.CONN_LISTEN = "LISTEN"

        mock_psutil.net_connections.side_effect = [[conn], []]

        # We need to mock sleep to speed up test
        with patch('time.sleep', return_value=None):
            result = self.manager.wait_for_port(4000, state="free", timeout=1)

        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
