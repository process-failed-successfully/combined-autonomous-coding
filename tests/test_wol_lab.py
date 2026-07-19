import unittest
from unittest.mock import patch, MagicMock
from shared.wol_lab import WolLabManager, run_wol_lab_logic
import argparse

class TestWolLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = WolLabManager()

    def test_validate_mac_valid(self):
        # Different valid formats
        macs = [
            "00:11:22:33:44:55",
            "00-11-22-33-44-55",
            "001122334455",
            "00:11:22:33:44:55".upper()
        ]
        for mac in macs:
            self.assertEqual(self.manager.validate_mac(mac), "001122334455")

    def test_validate_mac_invalid_length(self):
        # Too short
        with self.assertRaises(ValueError):
            self.manager.validate_mac("00:11:22:33:44")
        # Too long
        with self.assertRaises(ValueError):
            self.manager.validate_mac("00:11:22:33:44:55:66")

    def test_validate_mac_invalid_chars(self):
        # Invalid hex characters
        with self.assertRaises(ValueError):
            self.manager.validate_mac("00:11:22:33:44:ZZ")

    def test_build_magic_packet(self):
        mac = "00:11:22:33:44:55"
        packet = self.manager.build_magic_packet(mac)

        # Expected length: 6 bytes (FF) + 16 * 6 bytes (MAC) = 102 bytes
        self.assertEqual(len(packet), 102)

        # Check header
        self.assertEqual(packet[:6], b'\xff' * 6)

        # Check payload
        mac_bytes = bytes.fromhex("001122334455")
        self.assertEqual(packet[6:], mac_bytes * 16)

    @patch('shared.wol_lab.socket.socket')
    def test_wake_success(self, mock_socket_class):
        mock_sock = MagicMock()
        # Ensure the mock socket behaves as a context manager
        mock_socket_class.return_value.__enter__.return_value = mock_sock

        mac = "00:11:22:33:44:55"
        ip = "192.168.1.255"
        port = 7

        result = self.manager.wake(mac, ip_address=ip, port=port)

        self.assertTrue(result)
        mock_sock.setsockopt.assert_called_once()
        mock_sock.sendto.assert_called_once()

        # Check the arguments passed to sendto
        packet, address = mock_sock.sendto.call_args[0]
        self.assertEqual(address, (ip, port))
        self.assertEqual(len(packet), 102)

    @patch('shared.wol_lab.socket.socket')
    def test_wake_failure(self, mock_socket_class):
        mock_sock = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_sock
        # Simulate a socket error
        mock_sock.sendto.side_effect = Exception("Socket error")

        mac = "00:11:22:33:44:55"

        with self.assertRaises(RuntimeError):
            self.manager.wake(mac)

class TestWolLabLogic(unittest.TestCase):
    @patch('shared.wol_lab.WolLabManager.wake')
    def test_run_wol_lab_logic_success(self, mock_wake):
        mock_wake.return_value = True

        args = argparse.Namespace(mac="00:11:22:33:44:55", ip="255.255.255.255", port=9)
        result = run_wol_lab_logic(args)

        self.assertTrue(result)
        mock_wake.assert_called_once_with(mac_address="00:11:22:33:44:55", ip_address="255.255.255.255", port=9)

    @patch('shared.wol_lab.WolLabManager.wake')
    def test_run_wol_lab_logic_failure(self, mock_wake):
        mock_wake.side_effect = RuntimeError("Simulated failure")

        args = argparse.Namespace(mac="invalid_mac", ip="255.255.255.255", port=9)

        # We need to capture stderr to avoid cluttering test output,
        # but for simplicity in this case we'll just check the return value.
        with patch('sys.stderr', new=MagicMock()):
            result = run_wol_lab_logic(args)

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
