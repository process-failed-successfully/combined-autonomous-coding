import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import time
from shared.speed_lab import SpeedLabManager

class TestSpeedLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SpeedLabManager()

    @patch('shared.speed_lab.requests.get')
    def test_check_internet_speed_success(self, mock_get):
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Mock 1MB content
        mock_response.iter_content.return_value = [b'a' * 8192] * 128
        mock_get.return_value = mock_response

        # We can't easily mock time.time() difference to be non-zero predictable
        # so we rely on the logic calculating speed > 0

        result = self.manager.check_internet_speed()

        self.assertTrue(result['success'])
        self.assertAlmostEqual(result['size_bytes'], 8192 * 128)
        self.assertIn('speed_mbps', result)

    @patch('shared.speed_lab.requests.get')
    def test_check_internet_speed_failure(self, mock_get):
        mock_get.side_effect = Exception("Connection error")

        result = self.manager.check_internet_speed()

        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "Connection error")

    def test_check_disk_speed(self):
        # We'll use a very small size to keep test fast
        # 1MB
        result = self.manager.check_disk_speed(size_mb=1)

        self.assertTrue(result['success'])
        self.assertGreater(result['write_speed_mbps'], 0)
        self.assertGreater(result['read_speed_mbps'], 0)
        # Ensure file was cleaned up
        self.assertFalse(os.path.exists("speed_lab_test.tmp"))

    @patch('shared.speed_lab.socket.socket')
    def test_run_network_client(self, mock_socket_cls):
        mock_socket = MagicMock()
        mock_socket_cls.return_value.__enter__.return_value = mock_socket

        # Test client logic simply runs without error
        # It sends data in a loop until time expires

        # time.time calls:
        # 1. start_time = time.time()
        # 2. while time.time() < end_time (loop check 1)
        # 3. while time.time() < end_time (loop check 2)
        # 4. real_duration = time.time() - start_time

        with patch('time.time', side_effect=[100, 100.5, 102, 103]):
             # duration=1. end_time = 101.
             # 1. start=100
             # 2. 100.5 < 101 (True) -> send
             # 3. 102 < 101 (False) -> break
             # 4. real_duration = 103 - 100 = 3
             self.manager.run_network_client(host='localhost', port=1234, duration=1)

        # Verify connect called
        mock_socket.connect.assert_called_with(('localhost', 1234))
        # Verify sendall called
        self.assertTrue(mock_socket.sendall.called)

if __name__ == '__main__':
    unittest.main()
