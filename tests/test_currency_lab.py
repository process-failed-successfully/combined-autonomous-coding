import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402

from shared.currency_lab import CurrencyLabManager, run_currency_lab_logic  # noqa: E402


class TestCurrencyLab(unittest.TestCase):
    def setUp(self):
        self.manager = CurrencyLabManager()

    @patch("urllib.request.urlopen")
    def test_convert_static(self, mock_urlopen):
        # Test converting with static rates
        # USD -> EUR (1.0 -> 0.92)
        # 100 USD = 92 EUR
        mock_urlopen.side_effect = Exception("Network Error")

        result = self.manager.convert(100, "USD", "EUR")
        self.assertIn("92.00 EUR", result)
        self.assertIn("1 USD = 0.9200 EUR", result)
        self.assertIn("WARNING: Using static fallback rates", result)

        # Test unknown currency
        self.assertTrue(self.manager.convert(100, "XXX", "EUR").startswith("Error"))

        # Test negative amount
        self.assertTrue(self.manager.convert(-100, "USD", "EUR").startswith("Error"))

    @patch("urllib.request.urlopen")
    def test_convert_api_mocked(self, mock_urlopen):
        # Mock API response
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"result":"success","time_last_update_utc":"Some Time","rates":{"USD":1.0,"EUR":0.85}}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        manager = CurrencyLabManager()
        result = manager.convert(100, "USD", "EUR")
        self.assertIn("85.00 EUR", result)
        self.assertIn("1 USD = 0.8500 EUR", result)
        self.assertNotIn("WARNING", result) # Should not use fallback

    @patch("urllib.request.urlopen")
    def test_convert_api_failure(self, mock_urlopen):
        # Mock API failure
        mock_urlopen.side_effect = Exception("Network Error")

        manager = CurrencyLabManager()
        result = manager.convert(100, "USD", "EUR")
        self.assertIn("92.00 EUR", result) # Should fallback to static 0.92
        self.assertIn("WARNING: Using static fallback rates", result)

    def test_list_currencies(self):
        currencies = self.manager.list_currencies()
        self.assertIn("USD", currencies)
        self.assertIn("EUR", currencies)
        self.assertGreater(len(currencies), 10)

    @patch("sys.stdout")
    def test_cli_handler(self, mock_stdout):
        # Mock args for convert
        args_convert = MagicMock()
        args_convert.list = False
        args_convert.amount = "100"
        args_convert.from_cur = "USD"
        args_convert.to_cur = "EUR"
        self.assertTrue(run_currency_lab_logic(args_convert))

        # Mock args for list
        args_list = MagicMock()
        args_list.list = True
        self.assertTrue(run_currency_lab_logic(args_list))

        # Mock args for missing args
        args_missing = MagicMock()
        args_missing.list = False
        args_missing.amount = None
        args_missing.from_cur = None
        args_missing.to_cur = None

        with patch('sys.stderr') as mock_stderr:
            self.assertFalse(run_currency_lab_logic(args_missing))

        # Mock invalid amount
        args_invalid = MagicMock()
        args_invalid.list = False
        args_invalid.amount = "abc"
        args_invalid.from_cur = "USD"
        args_invalid.to_cur = "EUR"
        with patch('sys.stderr') as mock_stderr:
            self.assertFalse(run_currency_lab_logic(args_invalid))

if __name__ == '__main__':
    unittest.main()
