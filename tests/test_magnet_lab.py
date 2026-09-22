import unittest
from shared.magnet_lab import MagnetLabManager

class TestMagnetLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MagnetLabManager()

    def test_parse_valid_uri(self):
        uri = "magnet:?xt=urn:btih:cf438e86b71a20a20e0a203365c750cdf2b6c635&dn=example.txt&tr=http%3A%2F%2Ftracker.example.com%2Fannounce"
        parsed = self.manager.parse(uri)
        self.assertEqual(parsed["xt"], ["urn:btih:cf438e86b71a20a20e0a203365c750cdf2b6c635"])
        self.assertEqual(parsed["dn"], "example.txt")
        self.assertEqual(parsed["tr"], ["http://tracker.example.com/announce"])

    def test_parse_invalid_uri(self):
        with self.assertRaises(ValueError):
            self.manager.parse("http://example.com/file.torrent")

    def test_build_uri(self):
        xt = "urn:btih:cf438e86b71a20a20e0a203365c750cdf2b6c635"
        dn = "example.txt"
        tr = ["http://tracker.example.com/announce"]
        built = self.manager.build(xt=xt, dn=dn, tr=tr)
        expected = "magnet:?xt=urn%3Abtih%3Acf438e86b71a20a20e0a203365c750cdf2b6c635&dn=example.txt&tr=http%3A%2F%2Ftracker.example.com%2Fannounce"
        self.assertEqual(built, expected)

    def test_build_missing_xt(self):
        with self.assertRaises(ValueError):
            self.manager.build(xt="")

    def test_from_torrent(self):
        from shared.bencode_lab import BencodeManager
        torrent_data = BencodeManager.encode({
            "announce": b"http://tracker.example.com/announce",
            "info": {
                "name": b"example.txt",
                "length": 12345,
                "piece length": 262144,
                "pieces": b"12345678901234567890"
            }
        })

        magnet_uri = self.manager.from_torrent(torrent_data)
        self.assertIn("magnet:?", magnet_uri)
        self.assertIn("dn=example.txt", magnet_uri)
        self.assertIn("tr=http%3A%2F%2Ftracker.example.com%2Fannounce", magnet_uri)

if __name__ == '__main__':
    unittest.main()
