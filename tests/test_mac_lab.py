import unittest
from unittest.mock import patch, MagicMock
from shared.mac_lab import MacLabManager, run_mac_lab_logic
import argparse

class TestMacLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MacLabManager()

    def test_generate_default(self):
        macs = self.manager.generate(count=3)
        self.assertEqual(len(macs), 3)
        for mac in macs:
            self.assertTrue(self.manager.validate(mac))

    def test_generate_with_prefix(self):
        macs = self.manager.generate(count=1, prefix="00:1A:2B", format="colon")
        self.assertEqual(len(macs), 1)
        self.assertTrue(macs[0].startswith("00:1a:2b"))

    def test_format_mac(self):
        mac = "00:11:22:33:44:55"
        self.assertEqual(self.manager.format(mac, "hyphen"), "00-11-22-33-44-55")
        self.assertEqual(self.manager.format(mac, "dot"), "0011.2233.4455")
        self.assertEqual(self.manager.format(mac, "plain"), "001122334455")
        self.assertEqual(self.manager.format("001122334455", "colon"), "00:11:22:33:44:55")

    def test_validate_mac(self):
        self.assertTrue(self.manager.validate("00:11:22:33:44:55"))
        self.assertTrue(self.manager.validate("00-11-22-33-44-55"))
        self.assertTrue(self.manager.validate("0011.2233.4455"))
        self.assertTrue(self.manager.validate("001122334455"))

        self.assertFalse(self.manager.validate("00:11:22:33:44:5X")) # Invalid char
        self.assertFalse(self.manager.validate("00:11:22:33:44"))    # Too short
        self.assertFalse(self.manager.validate("00:11:22:33:44:55:66")) # Too long
        self.assertFalse(self.manager.validate("not_a_mac"))

    @patch('urllib.request.urlopen')
    def test_lookup_success(self, mock_urlopen):
        # Mock API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true, "found": true, "company": "Apple, Inc.", "country": "US", "address": "1 Infinite Loop"}'

        # Configure the context manager behavior for urlopen
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context_manager

        info = self.manager.lookup("00:1A:2B:3C:4D:5E")
        self.assertTrue(info["valid"])
        self.assertEqual(info["vendor"], "Apple, Inc.")
        self.assertEqual(info["country"], "US")

    @patch('urllib.request.urlopen')
    def test_lookup_not_found(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true, "found": false}'

        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context_manager

        info = self.manager.lookup("00:00:00:00:00:00")
        self.assertTrue(info["valid"])
        self.assertEqual(info["vendor"], "Unknown")

    def test_lookup_invalid_mac(self):
        info = self.manager.lookup("invalid_mac")
        self.assertFalse(info["valid"])
        self.assertIn("error", info)


class TestMacLabCLI(unittest.TestCase):
    @patch('builtins.print')
    def test_cli_generate(self, mock_print):
        args = argparse.Namespace(action="generate", count=2, prefix="", format="colon")
        try:
            run_mac_lab_logic(args)
        except SystemExit:
            pass
        self.assertEqual(mock_print.call_count, 2)

    @patch('builtins.print')
    def test_cli_format(self, mock_print):
        args = argparse.Namespace(action="format", mac="001122334455", format="colon")
        try:
            run_mac_lab_logic(args)
        except SystemExit:
            pass
        mock_print.assert_called_with("00:11:22:33:44:55")

    @patch('builtins.print')
    @patch('sys.exit')
    def test_cli_validate_valid(self, mock_exit, mock_print):
        args = argparse.Namespace(action="validate", mac="00:11:22:33:44:55")
        run_mac_lab_logic(args)
        mock_print.assert_called_with("✅ Valid MAC Address: 00:11:22:33:44:55")
        mock_exit.assert_called_with(0)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_cli_validate_invalid(self, mock_exit, mock_print):
        args = argparse.Namespace(action="validate", mac="invalid")
        run_mac_lab_logic(args)
        mock_print.assert_called_with("❌ Invalid MAC Address: invalid")
        mock_exit.assert_called_with(1)

    @patch('builtins.print')
    @patch('urllib.request.urlopen')
    def test_cli_lookup(self, mock_urlopen, mock_print):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true, "found": true, "company": "Apple, Inc.", "country": "US", "address": "1 Infinite Loop"}'

        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context_manager

        args = argparse.Namespace(action="lookup", mac="00:1A:2B:3C:4D:5E")
        try:
            run_mac_lab_logic(args)
        except SystemExit:
            pass

        # Verify it printed the vendor info
        mock_print.assert_any_call("  Vendor: Apple, Inc.")

if __name__ == '__main__':
    unittest.main()
