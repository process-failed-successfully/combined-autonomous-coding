import unittest
import pytest
from unittest.mock import patch
import argparse

pytest.importorskip("phonenumbers")

from shared.phone_lab import PhoneLabManager, run_phone_lab_logic

class TestPhoneLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = PhoneLabManager()

    def test_parse_valid(self):
        parsed = self.manager.parse("+14155552671")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.country_code, 1)
        self.assertEqual(parsed.national_number, 4155552671)

    def test_parse_with_region(self):
        parsed = self.manager.parse("020 7946 0958", region="GB")
        self.assertEqual(parsed.country_code, 44)
        self.assertEqual(parsed.national_number, 2079460958)

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.parse("not_a_number")

    def test_is_valid(self):
        self.assertTrue(self.manager.is_valid("+14155552671"))
        self.assertTrue(self.manager.is_valid("4155552671", region="US"))
        self.assertFalse(self.manager.is_valid("+1415555267")) # Too short
        self.assertFalse(self.manager.is_valid("not a number"))

    def test_format(self):
        phone = "4155552671"
        region = "US"
        self.assertEqual(self.manager.format(phone, region, "e164"), "+14155552671")
        self.assertEqual(self.manager.format(phone, region, "national"), "(415) 555-2671")
        self.assertEqual(self.manager.format(phone, region, "international"), "+1 415-555-2671")
        self.assertEqual(self.manager.format(phone, region, "rfc3966"), "tel:+1-415-555-2671")

    def test_get_info(self):
        info = self.manager.get_info("+14155552671")
        self.assertTrue(info["valid"])
        self.assertTrue(info["possible"])
        self.assertEqual(info["country_code"], 1)
        self.assertEqual(info["national_number"], 4155552671)
        self.assertEqual(info["e164"], "+14155552671")
        self.assertEqual(info["region_code"], "US")
        # Depending on the phonenumbers db, type could be FIXED_LINE_OR_MOBILE or something else, just assert it's present
        self.assertTrue(info.get("type"))
        self.assertEqual(info["location"], "San Francisco, CA")

    def test_get_info_invalid(self):
        info = self.manager.get_info("123", region="US")
        self.assertFalse(info["valid"])
        self.assertFalse(info["possible"])
        self.assertEqual(info["type"], "Unknown")
        self.assertIsNone(info["region_code"])


class TestPhoneLabCLI(unittest.TestCase):
    @patch('builtins.print')
    def test_cli_parse(self, mock_print):
        args = argparse.Namespace(action="parse", phone="4155552671", region="US")
        try:
            run_phone_lab_logic(args)
        except SystemExit:
            pass
        self.assertTrue(mock_print.called)

    @patch('builtins.print')
    def test_cli_format(self, mock_print):
        args = argparse.Namespace(action="format", phone="4155552671", region="US", format="e164")
        try:
            run_phone_lab_logic(args)
        except SystemExit:
            pass
        mock_print.assert_called_with("+14155552671")

    @patch('builtins.print')
    @patch('sys.exit')
    def test_cli_validate_valid(self, mock_exit, mock_print):
        args = argparse.Namespace(action="validate", phone="+14155552671", region=None)
        run_phone_lab_logic(args)
        mock_print.assert_called_with("✅ Valid Phone Number: +14155552671")
        mock_exit.assert_called_with(0)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_cli_validate_invalid(self, mock_exit, mock_print):
        args = argparse.Namespace(action="validate", phone="invalid", region=None)
        run_phone_lab_logic(args)
        mock_print.assert_called_with("❌ Invalid Phone Number: invalid")
        mock_exit.assert_called_with(1)

    @patch('builtins.print')
    def test_cli_info(self, mock_print):
        args = argparse.Namespace(action="info", phone="+14155552671", region=None)
        try:
            run_phone_lab_logic(args)
        except SystemExit:
            pass
        self.assertTrue(mock_print.called)

if __name__ == '__main__':
    unittest.main()
