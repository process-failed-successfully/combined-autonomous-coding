import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import json
import urllib.error
from shared.mac_lab import MacLabManager, run_mac_lab_logic
import argparse

class TestMacLab(unittest.TestCase):
    def setUp(self):
        self.manager = MacLabManager()

    def test_validate_mac(self):
        self.assertTrue(self.manager.validate("00:1A:2B:3C:4D:5E"))
        self.assertTrue(self.manager.validate("00-1A-2B-3C-4D-5E"))
        self.assertTrue(self.manager.validate("001A2B3C4D5E"))
        self.assertTrue(self.manager.validate("001a.2b3c.4d5e"))
        self.assertTrue(self.manager.validate("aa:bb:cc:dd:ee:ff"))

        self.assertFalse(self.manager.validate("00:1A:2B:3C:4D:5G")) # Invalid hex
        self.assertFalse(self.manager.validate("00:1A:2B:3C:4D")) # Too short
        self.assertFalse(self.manager.validate("00:1A:2B:3C:4D:5E:6F")) # Too long
        self.assertFalse(self.manager.validate(""))

    def test_format_mac(self):
        # Default format
        self.assertEqual(self.manager.format_mac("001a2b3c4d5e"), "00:1a:2b:3c:4d:5e")

        # Uppercase
        self.assertEqual(self.manager.format_mac("001a2b3c4d5e", uppercase=True), "00:1A:2B:3C:4D:5E")

        # Dash separator
        self.assertEqual(self.manager.format_mac("00:1a:2b:3c:4d:5e", separator="-"), "00-1a-2b-3c-4d-5e")

        # Cisco style
        self.assertEqual(self.manager.format_mac("00:1a:2b:3c:4d:5e", separator="."), "001a.2b3c.4d5e")

        # Invalid
        with self.assertRaises(ValueError):
            self.manager.format_mac("invalid")

    def test_generate_mac(self):
        # Single generation
        macs = self.manager.generate()
        self.assertEqual(len(macs), 1)
        self.assertTrue(self.manager.validate(macs[0]))

        # Multiple generation
        macs = self.manager.generate(count=3)
        self.assertEqual(len(macs), 3)
        for mac in macs:
            self.assertTrue(self.manager.validate(mac))

        # With prefix
        prefix = "00:1A:2B"
        macs = self.manager.generate(prefix=prefix, uppercase=True)
        self.assertTrue(macs[0].startswith("00:1A:2B"))

        # Invalid prefix
        with self.assertRaises(ValueError):
            self.manager.generate(prefix="invalid")

    @patch('urllib.request.urlopen')
    def test_lookup_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "result": {
                "company": "Apple, Inc.",
                "mac_prefix": "00:1A:2B",
                "address": "1 Infinite Loop, Cupertino, CA 95014, US"
            }
        }).encode('utf-8')
        # __enter__ and __exit__ for context manager
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.manager.lookup("00:1A:2B:3C:4D:5E")
        self.assertEqual(result["company"], "Apple, Inc.")
        self.assertEqual(result["mac"], "00:1A:2B:3C:4D:5E")

    @patch('urllib.request.urlopen')
    def test_lookup_not_found(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "result": {
                "error": "No vendor found"
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.manager.lookup("00:00:00:00:00:00")
        self.assertEqual(result["company"], "Not Found")

    @patch('urllib.request.urlopen')
    def test_lookup_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = self.manager.lookup("00:1A:2B:3C:4D:5E")
        self.assertEqual(result["company"], "Error")
        self.assertIn("Connection refused", result["error"])

    # --- CLI Logic Tests ---
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_validate_success(self, mock_stdout):
        args = argparse.Namespace(action="validate", mac="00:1A:2B:3C:4D:5E")
        with self.assertRaises(SystemExit) as cm:
            run_mac_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("VALID", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_cli_validate_failure(self, mock_stderr):
        args = argparse.Namespace(action="validate", mac="invalid")
        # For validation, run_mac_lab_logic prints failure to stdout, but let's just check exit code and output
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_mac_lab_logic(args)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("INVALID", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_generate(self, mock_stdout):
        args = argparse.Namespace(action="generate", count=2, prefix=None, upper=False, separator=":")
        with self.assertRaises(SystemExit) as cm:
            run_mac_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue().strip().split('\n')
        self.assertEqual(len(output), 2)

if __name__ == '__main__':
    unittest.main()
