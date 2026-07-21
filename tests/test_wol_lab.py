import unittest
from unittest.mock import patch, MagicMock
import socket
from shared.wol_lab import WolLabManager

class TestWolLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = WolLabManager()

    def test_clean_mac_valid(self):
        valid_macs = [
            "00:11:22:33:44:55",
            "00-11-22-33-44-55",
            "0011.2233.4455",
            "001122334455",
            "AA:BB:CC:DD:EE:FF",
            "aabbccddeeff"
        ]
        for mac in valid_macs:
            cleaned = self.manager._clean_mac(mac)
            self.assertEqual(len(cleaned), 12)
            self.assertEqual(cleaned.lower(), "001122334455" if "00" in mac else "aabbccddeeff")

    def test_clean_mac_invalid(self):
        invalid_macs = [
            "00:11:22:33:44", # too short
            "00:11:22:33:44:55:66", # too long
            "00:11:22:33:44:ZZ", # invalid char
            "not a mac address"
        ]
        for mac in invalid_macs:
            with self.assertRaises(ValueError):
                self.manager._clean_mac(mac)

    def test_create_magic_packet(self):
        mac = "01:23:45:67:89:ab"
        packet = self.manager.create_magic_packet(mac)

        self.assertEqual(len(packet), 102)

        # Check header
        self.assertEqual(packet[:6], b'\xff' * 6)

        # Check payload
        mac_bytes = bytes.fromhex("0123456789ab")
        self.assertEqual(packet[6:], mac_bytes * 16)

    @patch('socket.socket')
    def test_send_magic_packet_success(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket_class.return_value.__enter__.return_value = mock_socket

        mac = "00:11:22:33:44:55"
        ip = "192.168.1.255"
        port = 9

        result = self.manager.send_magic_packet(mac, ip, port)

        self.assertTrue(result)

        # Verify socket setup
        mock_socket_class.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM)
        mock_socket.setsockopt.assert_called_with(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Verify packet sent
        packet = self.manager.create_magic_packet(mac)
        mock_socket.sendto.assert_called_with(packet, (ip, port))

    @patch('socket.socket')
    def test_send_magic_packet_failure(self, mock_socket_class):
        mock_socket_class.side_effect = Exception("Socket error")

        result = self.manager.send_magic_packet("00:11:22:33:44:55")

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
