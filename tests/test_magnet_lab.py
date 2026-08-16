import unittest
from shared.magnet_lab import MagnetLabManager


class TestMagnetLabManager(unittest.TestCase):
    def test_parse_valid(self):
        uri = "magnet:?xt=urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97&dn=ubuntu-20.04.1-desktop-amd64.iso&tr=http%3A%2F%2Ftorrent.ubuntu.com%3A6969%2Fannounce&tr=http%3A%2F%2Fipv6.torrent.ubuntu.com%3A6969%2Fannounce"
        parsed = MagnetLabManager.parse(uri)

        self.assertEqual(parsed['xt'], ['urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97'])
        self.assertEqual(parsed['dn'], 'ubuntu-20.04.1-desktop-amd64.iso')
        self.assertEqual(parsed['tr'], ['http://torrent.ubuntu.com:6969/announce', 'http://ipv6.torrent.ubuntu.com:6969/announce'])

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            MagnetLabManager.parse("http://example.com/torrent.torrent")

    def test_build_valid(self):
        components = {
            'xt': 'urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97',
            'dn': 'ubuntu-20.04.1-desktop-amd64.iso',
            'tr': ['http://torrent.ubuntu.com:6969/announce']
        }
        uri = MagnetLabManager.build(components)
        self.assertIn("magnet:?", uri)
        self.assertIn("xt=urn:btih:b9968411c52112e4f0ddfc9a1e04e4c27b08dd97", uri)
        self.assertIn("dn=ubuntu-20.04.1-desktop-amd64.iso", uri)
        self.assertIn("tr=http%3A//torrent.ubuntu.com%3A6969/announce", uri)

    def test_build_invalid(self):
        with self.assertRaises(ValueError):
            MagnetLabManager.build({})

    def test_from_torrent(self):
        # Create a mock torrent file using BencodeManager
        from shared.bencode_lab import BencodeManager

        info = {
            'name': b'test.txt',
            'piece length': 262144,
            'pieces': b'12345678901234567890',
            'length': 12
        }

        torrent_dict = {
            'announce': b'http://tracker.example.com/announce',
            'info': info
        }

        manager = BencodeManager()
        torrent_data = manager.encode(torrent_dict)

        uri = MagnetLabManager.from_torrent(torrent_data)

        self.assertIn("magnet:?", uri)
        self.assertIn("dn=test.txt", uri)
        self.assertIn("tr=http%3A//tracker.example.com/announce", uri)
        self.assertIn("xt=urn:btih:", uri)

if __name__ == '__main__':
    unittest.main()
