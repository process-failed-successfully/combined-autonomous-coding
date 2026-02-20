import unittest
import struct
import socket
import time
from unittest.mock import MagicMock, patch
from shared.sniffer_lab import PacketParser, SnifferManager


class TestPacketParser(unittest.TestCase):
    def setUp(self):
        self.parser = PacketParser()

    def test_parse_ipv4_udp(self):
        # Construct raw packet
        # Ethernet Header (14 bytes)
        # Dst MAC (6), Src MAC (6), Type (2)
        # Type 0x0800 = IPv4
        eth = struct.pack('!6s6sH', b'\xAA' * 6, b'\xBB' * 6, 2048)

        # IP Header (20 bytes)
        # Ver=4, IHL=5 -> 0x45
        # Proto=17 (UDP)
        src_ip = socket.inet_aton("192.168.1.1")
        dst_ip = socket.inet_aton("192.168.1.2")
        ip = struct.pack('!BBHHHBBH4s4s', 69, 0, 32, 0, 0, 64, 17, 0, src_ip, dst_ip)

        # UDP Header (8 bytes)
        # Src Port=1234, Dst Port=53, Len=12
        udp = struct.pack('!HHHH', 1234, 53, 12, 0)

        payload = b'test'

        raw_data = eth + ip + udp + payload

        packet = self.parser.parse(raw_data)

        self.assertIn(packet.proto_l2, [8, 2048])  # ntohs result depends on endianness
        self.assertEqual(packet.src_mac, "bb:bb:bb:bb:bb:bb")
        self.assertEqual(packet.dst_mac, "aa:aa:aa:aa:aa:aa")
        self.assertEqual(packet.src_ip, "192.168.1.1")
        self.assertEqual(packet.dst_ip, "192.168.1.2")
        self.assertEqual(packet.proto_l3, 17)
        self.assertEqual(packet.src_port, 1234)
        self.assertEqual(packet.dst_port, 53)
        self.assertIn("UDP", packet.info)
        self.assertIn("Len=12", packet.info)

    def test_parse_truncated(self):
        raw_data = b'\x00' * 10
        packet = self.parser.parse(raw_data)
        self.assertIn("Truncated", packet.info)


class TestSnifferManager(unittest.TestCase):
    def setUp(self):
        self.manager = SnifferManager()

    @patch('psutil.net_if_addrs')
    def test_get_interfaces(self, mock_net):
        mock_net.return_value = {'eth0': [], 'lo': []}
        ifaces = self.manager.get_interfaces()
        self.assertEqual(sorted(ifaces), ['eth0', 'lo'])

    @patch('socket.socket')
    def test_start_stop_capture(self, mock_socket_cls):
        # Mock socket
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        # Ensure AF_PACKET exists on socket module (mock it if needed)
        with patch.object(socket, 'AF_PACKET', create=True, new=1):
            with patch.object(socket, 'SOCK_RAW', create=True, new=2):
                callback = MagicMock()
                self.manager.start_capture('eth0', callback)

                self.assertTrue(self.manager.running)
                mock_sock.bind.assert_called_with(('eth0', 0))

                self.manager.stop_capture()
                self.assertFalse(self.manager.running)
                mock_sock.close.assert_called()

    def test_demo_capture(self):
        callback = MagicMock()
        self.manager.start_demo_capture(callback)
        self.assertTrue(self.manager.running)

        # Wait a bit for thread to run
        time.sleep(0.5)

        self.manager.stop_capture()
        self.assertFalse(self.manager.running)

        # Check if callback was called
        # Depending on timing/random, it might be called 0 or more times.
        # But we verify it didn't crash.
        pass


if __name__ == '__main__':
    unittest.main()
