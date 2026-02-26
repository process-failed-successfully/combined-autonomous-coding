
import unittest
import struct
import tempfile
import os
from pathlib import Path
from shared.pcap_lab import PcapLabManager

class TestPcapLab(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.pcap_path = Path(self.tmp_dir.name) / "test.pcap"
        self._create_mock_pcap(self.pcap_path)
        self.manager = PcapLabManager()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_mock_pcap(self, path: Path):
        """Creates a valid minimal PCAP file with one UDP packet."""
        # Global Header
        # Magic(4) + VerMaj(2) + VerMin(2) + Zone(4) + SigFigs(4) + SnapLen(4) + Network(4)
        gh = struct.pack('<IHHiIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)

        # Packet Data (Ethernet + IPv4 + UDP)
        # Ethernet (14)
        eth = b'\x00\x00\x00\x00\x00\x02' + b'\x00\x00\x00\x00\x00\x01' + b'\x08\x00'
        # IPv4 (20)
        # 1.1.1.1 -> 2.2.2.2
        ipv4 = b'\x45\x00\x00\x1c' + b'\x00\x00\x00\x00' + b'\x40\x11\x00\x00' + \
               b'\x01\x01\x01\x01' + b'\x02\x02\x02\x02'
        # UDP (8)
        # 8080 -> 80
        udp = struct.pack('!HHHH', 8080, 80, 8, 0)

        pkt_data = eth + ipv4 + udp

        # Packet Header
        # TsSec(4) + TsUsec(4) + InclLen(4) + OrigLen(4)
        ph = struct.pack('<IIII', 1600000000, 0, len(pkt_data), len(pkt_data))

        with open(path, 'wb') as f:
            f.write(gh)
            f.write(ph)
            f.write(pkt_data)

    def test_analyze(self):
        stats = self.manager.analyze(self.pcap_path)
        self.assertEqual(stats['packet_count'], 1)
        self.assertEqual(stats['protocols']['UDP'], 1)
        self.assertIn('1.1.1.1', stats['src_ips'])
        self.assertIn('2.2.2.2', stats['dst_ips'])

    def test_list_packets(self):
        pkts = list(self.manager.list_packets(self.pcap_path))
        self.assertEqual(len(pkts), 1)
        p = pkts[0]
        self.assertEqual(p['proto'], 'UDP')
        self.assertEqual(p['src'], '1.1.1.1')
        self.assertEqual(p['dst'], '2.2.2.2')
        self.assertIn('UDP 8080 -> 80', p['summary'])

    def test_filter_packets_match(self):
        # Match Protocol
        pkts = list(self.manager.filter_packets(self.pcap_path, proto='UDP'))
        self.assertEqual(len(pkts), 1)

        # Match Src
        pkts = list(self.manager.filter_packets(self.pcap_path, src='1.1.1.1'))
        self.assertEqual(len(pkts), 1)

    def test_filter_packets_no_match(self):
        # No Match Protocol
        pkts = list(self.manager.filter_packets(self.pcap_path, proto='TCP'))
        self.assertEqual(len(pkts), 0)

        # No Match IP
        pkts = list(self.manager.filter_packets(self.pcap_path, src='9.9.9.9'))
        self.assertEqual(len(pkts), 0)

    def test_invalid_file(self):
        res = self.manager.analyze(Path("nonexistent.pcap"))
        self.assertIn("error", res)

if __name__ == '__main__':
    unittest.main()
