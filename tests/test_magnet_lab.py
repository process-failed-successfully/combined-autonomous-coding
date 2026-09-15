import unittest
from shared.magnet_lab import MagnetLabManager

class TestMagnetLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MagnetLabManager()

    def test_parse_valid_uri(self):
        uri = "magnet:?xt=urn:btih:12345&dn=test.file&tr=http://tracker1.com&tr=http://tracker2.com"
        result = self.manager.parse(uri)
        self.assertEqual(result['xt'], "urn:btih:12345")
        self.assertEqual(result['info_hash'], "urn:btih:12345")
        self.assertEqual(result['hash'], "12345")
        self.assertEqual(result['dn'], "test.file")
        self.assertEqual(result['name'], "test.file")
        self.assertEqual(result['tr'], ["http://tracker1.com", "http://tracker2.com"])
        self.assertEqual(result['trackers'], ["http://tracker1.com", "http://tracker2.com"])

    def test_parse_invalid_uri(self):
        uri = "http://not.a.magnet.link"
        with self.assertRaises(ValueError):
            self.manager.parse(uri)

    def test_build_uri(self):
        data = {
            'xt': 'urn:btih:abcde',
            'dn': 'example',
            'tr': ['udp://tracker.openbittorrent.com:80']
        }
        uri = self.manager.build(data)
        self.assertTrue(uri.startswith("magnet:?"))
        self.assertIn("xt=urn%3Abtih%3Aabcde", uri)
        self.assertIn("dn=example", uri)
        self.assertIn("tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80", uri)

    def test_build_uri_convenience(self):
        data = {
            'hash': 'abcde',
            'name': 'example',
            'trackers': ['udp://tracker.openbittorrent.com:80']
        }
        uri = self.manager.build(data)
        self.assertTrue(uri.startswith("magnet:?"))
        self.assertIn("xt=urn%3Abtih%3Aabcde", uri)
        self.assertIn("dn=example", uri)
        self.assertIn("tr=udp%3A%2F%2Ftracker.openbittorrent.com%3A80", uri)

    def test_from_torrent(self):
        # A simple bencoded dictionary simulating a torrent file
        # d4:infod4:name9:test_file6:lengthi123eee
        torrent_data = b"d4:infod4:name9:test_file6:lengthi123eee"
        uri = self.manager.from_torrent(torrent_data)
        self.assertTrue(uri.startswith("magnet:?"))
        self.assertIn("dn=test_file", uri)
        self.assertIn("xt=urn%3Abtih%3A", uri)

if __name__ == '__main__':
    unittest.main()
