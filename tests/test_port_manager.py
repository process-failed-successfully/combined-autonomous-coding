import unittest
from unittest.mock import MagicMock, patch
from shared.port_manager import PortManager

class TestPortManager(unittest.TestCase):

    @patch('shared.port_manager.psutil.net_connections')
    @patch('shared.port_manager.psutil.Process')
    def test_list_listening_ports(self, mock_process, mock_net_connections):
        # Mock connections
        conn1 = MagicMock()
        conn1.status = 'LISTEN'
        conn1.pid = 1234
        conn1.laddr.port = 8080
        conn1.type = 1 # TCP

        conn2 = MagicMock()
        conn2.status = 'ESTABLISHED' # Should be ignored

        mock_net_connections.return_value = [conn1, conn2]

        # Mock process
        proc_mock = MagicMock()
        proc_mock.name.return_value = "test_process"
        mock_process.return_value = proc_mock

        ports = PortManager.list_listening_ports()

        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['port'], 8080)
        self.assertEqual(ports[0]['pid'], 1234)
        self.assertEqual(ports[0]['name'], "test_process")
        self.assertEqual(ports[0]['type'], "TCP")

    @patch('shared.port_manager.psutil.net_connections')
    @patch('shared.port_manager.psutil.Process')
    def test_check_port(self, mock_process, mock_net_connections):
        conn = MagicMock()
        conn.status = 'LISTEN'
        conn.pid = 5678
        conn.laddr.port = 3000
        mock_net_connections.return_value = [conn]

        mock_process.return_value.name.return_value = "node"

        # Check existing port
        info = PortManager.check_port(3000)
        self.assertIsNotNone(info)
        self.assertEqual(info['pid'], 5678)
        self.assertEqual(info['name'], "node")

        # Check non-existing port
        info_none = PortManager.check_port(9000)
        self.assertIsNone(info_none)

    @patch('shared.port_manager.PortManager.check_port')
    @patch('shared.port_manager.psutil.Process')
    def test_kill_port(self, mock_process, mock_check_port):
        # Case 1: Port not in use
        mock_check_port.return_value = None
        self.assertFalse(PortManager.kill_port(8000))

        # Case 2: Port in use, successful kill
        mock_check_port.return_value = {'pid': 100, 'name': 'app', 'port': 8000}
        proc_instance = MagicMock()
        mock_process.return_value = proc_instance

        self.assertTrue(PortManager.kill_port(8000))
        proc_instance.terminate.assert_called_once()
        proc_instance.wait.assert_called_once()

    @patch('shared.port_manager.PortManager.check_port')
    @patch('time.sleep') # Don't actually sleep
    @patch('time.time')
    def test_wait_for_port_free(self, mock_time, mock_sleep, mock_check_port):
        # Mock time to advance: 0, 1, 2...
        mock_time.side_effect = [0, 1, 2, 3, 4]

        # Port is active initially, then becomes free (None)
        mock_check_port.side_effect = [{'pid': 1}, None]

        self.assertTrue(PortManager.wait_for_port(3000, state='free'))

    @patch('shared.port_manager.PortManager.check_port')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_port_timeout(self, mock_time, mock_sleep, mock_check_port):
        # Mock time to start at 0 and check condition is > timeout
        mock_time.side_effect = [0, 100] # Timeout default is 30

        # Port stays active (we want free)
        mock_check_port.return_value = {'pid': 1}

        self.assertFalse(PortManager.wait_for_port(3000, state='free'))

if __name__ == '__main__':
    unittest.main()
