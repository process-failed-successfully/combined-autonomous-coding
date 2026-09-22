import unittest
import os
import tempfile
import sys
from unittest.mock import patch
from io import StringIO
from shared.magnet_lab import MagnetLabManager, run_magnet_lab_logic
from shared.bencode_lab import BencodeManager

class TestMagnetLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MagnetLabManager()

    def test_parse_valid(self):
        uri = "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10&dn=Sintel&tr=udp%3A%2F%2Fexplodie.org%3A6969"
        res = self.manager.parse(uri)
        self.assertTrue(res["success"])
        self.assertIn("xt", res["parsed"])
        self.assertEqual(res["parsed"]["xt"][0], "urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10")
        self.assertEqual(res["parsed"]["dn"][0], "Sintel")
        self.assertEqual(res["parsed"]["tr"][0], "udp://explodie.org:6969")

    def test_parse_invalid(self):
        res = self.manager.parse("notamagnet:?xt=foo")
        self.assertFalse(res.get("success"))
        self.assertIn("error", res)

    def test_build_basic(self):
        params = {
            "xt": "urn:btih:test",
            "dn": "test_name"
        }
        res = self.manager.build(params)
        self.assertTrue(res.startswith("magnet:?"))
        self.assertIn("xt=urn%3Abtih%3Atest", res)
        self.assertIn("dn=test_name", res)

    def test_build_list_params(self):
        params = {
            "xt": "urn:btih:test",
            "tr": ["http://tracker1", "http://tracker2"]
        }
        res = self.manager.build(params)
        self.assertIn("tr=http%3A%2F%2Ftracker1", res)
        self.assertIn("tr=http%3A%2F%2Ftracker2", res)

    def test_from_torrent(self):
        # Create a dummy torrent
        b = BencodeManager()
        data = {
            "info": {
                "name": "test_torrent",
                "piece length": 256,
                "pieces": b"12345678901234567890"
            },
            "announce": "http://tracker.com/announce"
        }

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b.encode(data))
            temp_name = f.name

        try:
            res = self.manager.from_torrent(temp_name)
            self.assertTrue(res["success"])
            self.assertEqual(res["name"], "test_torrent")
            self.assertEqual(res["trackers"], ["http://tracker.com/announce"])
            self.assertTrue(res["uri"].startswith("magnet:?"))
        finally:
            os.remove(temp_name)

    def test_from_torrent_bytes_keys(self):
        # Create a dummy torrent using bytes keys to test handling of raw decoded bencode
        # BencodeManager actually returns string keys where possible, but if not possible
        # or if forced, it could be bytes. We simulate what happens if the parsed dict has byte keys.
        b = BencodeManager()
        # To force BencodeManager to encode bytes keys, we pass a dict with bytes keys.
        # Although Python's BencodeManager encode method handles bytes keys, let's just make
        # sure the from_torrent method can handle a mocked bdecode that returns bytes keys.
        with patch.object(b, 'decode') as mock_decode:
            mock_decode.return_value = {
                b'info': {b'name': b'test_torrent_bytes'},
                b'announce-list': [[b'http://tracker1'], [b'http://tracker2']]
            }
            with patch('shared.magnet_lab.BencodeManager') as MockBencodeManager:
                MockBencodeManager.return_value = b

                with tempfile.NamedTemporaryFile(delete=False) as f:
                    f.write(b"dummy")
                    temp_name = f.name
                try:
                    res = self.manager.from_torrent(temp_name)
                    self.assertTrue(res["success"])
                    self.assertEqual(res["name"], "test_torrent_bytes")
                    self.assertEqual(res["trackers"], ["http://tracker1", "http://tracker2"])
                finally:
                    os.remove(temp_name)

class TestMagnetLabLogic(unittest.TestCase):

    class Args:
        pass

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_parse(self, mock_stdout):
        args = self.Args()
        args.action = "parse"
        args.uri = "magnet:?xt=urn:btih:test"

        success = run_magnet_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("urn:btih:test", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_build(self, mock_stdout):
        args = self.Args()
        args.action = "build"
        args.xt = "urn:btih:test"
        args.dn = "name"
        args.tr = ["http://tracker"]

        success = run_magnet_lab_logic(args)
        self.assertTrue(success)
        self.assertIn("magnet:?", mock_stdout.getvalue())
        self.assertIn("dn=name", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
