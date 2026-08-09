import unittest
from unittest.mock import patch, mock_open, MagicMock
from shared.magnet_lab import MagnetLabManager, run_magnet_lab_logic
import sys
import io

class TestMagnetLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = MagnetLabManager()

    def test_parse_valid(self):
        uri = "magnet:?xt=urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101&dn=ubuntu-19.10-desktop-amd64.iso&tr=https%3A%2F%2Ftorrent.ubuntu.com%2Fannounce"
        result = self.manager.parse(uri)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["xt"][0], "urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101")
        self.assertEqual(result["result"]["dn"], "ubuntu-19.10-desktop-amd64.iso")
        self.assertEqual(result["result"]["tr"][0], "https://torrent.ubuntu.com/announce")

    def test_parse_invalid(self):
        uri = "http://example.com/file.torrent"
        result = self.manager.parse(uri)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Not a valid magnet URI.")

    def test_build_valid_urn(self):
        result = self.manager.build("urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101", "ubuntu.iso", ["http://tracker.com"])
        self.assertTrue(result["success"])
        self.assertIn("xt=urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101", result["uri"])
        self.assertIn("dn=ubuntu.iso", result["uri"])
        self.assertIn("tr=http%3A//tracker.com", result["uri"])

    def test_build_valid_hex(self):
        result = self.manager.build("b415c913643e5ff49fe37d304bbb5e6e11ad5101")
        self.assertTrue(result["success"])
        self.assertIn("xt=urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101", result["uri"])

    def test_build_invalid_hex(self):
        result = self.manager.build("short")
        self.assertFalse(result["success"])

    @patch('pathlib.Path.is_file', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data=b'd8:announce18:http://tracker.com4:infod4:name10:ubuntu.isoe')
    @patch('shared.bencode_lab.BencodeManager.decode')
    @patch('shared.bencode_lab.BencodeManager.encode', return_value=b'd4:name10:ubuntu.isoe')
    def test_from_torrent(self, mock_encode, mock_decode, mock_file, mock_is_file):
        # Mock BencodeManager to return a simple dict structure
        mock_decode.return_value = {
            b'announce': b'http://tracker.com',
            b'info': {
                b'name': b'ubuntu.iso'
            }
        }

        result = self.manager.from_torrent("dummy.torrent")
        self.assertTrue(result["success"])
        # Info hash is sha1 of b'd4:name10:ubuntu.isoe'
        self.assertIn("xt=urn:btih:", result["uri"])
        self.assertIn("dn=ubuntu.iso", result["uri"])
        self.assertIn("tr=http%3A//tracker.com", result["uri"])

class TestMagnetLabCLI(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_parse(self, mock_stdout):
        args = MagicMock()
        args.action = "parse"
        args.uri = "magnet:?xt=urn:btih:123"

        with patch('sys.exit') as mock_exit:
            run_magnet_lab_logic(args)
            mock_exit.assert_not_called()
        self.assertIn('"xt"', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_build(self, mock_stdout):
        args = MagicMock()
        args.action = "build"
        args.info_hash = "b415c913643e5ff49fe37d304bbb5e6e11ad5101"
        args.name = ""
        args.trackers = []

        with patch('sys.exit') as mock_exit:
            run_magnet_lab_logic(args)
            mock_exit.assert_not_called()
        self.assertIn("magnet:?xt=urn:btih:b415c913643e5ff49fe37d304bbb5e6e11ad5101", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
