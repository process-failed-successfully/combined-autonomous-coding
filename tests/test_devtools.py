import unittest
from shared.devtools import DevTools
from datetime import datetime


class TestDevTools(unittest.TestCase):

    def test_epoch_to_date(self):
        ts = 1678886400.0  # 2023-03-15 13:20:00 UTC (approx)
        res = DevTools.epoch_to_date(ts)
        self.assertIn("2023-03-15", res)

    def test_date_to_epoch(self):
        date_str = "2023-03-15 13:20:00"
        ts = DevTools.date_to_epoch(date_str)
        self.assertIsInstance(ts, float)
        self.assertEqual(ts, datetime(2023, 3, 15, 13, 20, 0).timestamp())

    def test_base64_encode(self):
        text = "Hello World"
        encoded = DevTools.base64_encode(text)
        self.assertEqual(encoded, "SGVsbG8gV29ybGQ=")

    def test_base64_decode(self):
        encoded = "SGVsbG8gV29ybGQ="
        decoded = DevTools.base64_decode(encoded)
        self.assertEqual(decoded, "Hello World")

    def test_generate_uuid(self):
        uuid_str = DevTools.generate_uuid()
        self.assertEqual(len(uuid_str), 36)
        self.assertIn("-", uuid_str)

    def test_calculate_hash(self):
        text = "hello"
        # sha256 of "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(DevTools.calculate_hash(text, "sha256"), expected)

    def test_format_json(self):
        ugly_json = '{"a":1, "b": 2}'
        pretty_json = DevTools.format_json(ugly_json)
        self.assertIn('\n', pretty_json)
        self.assertIn('  "a": 1', pretty_json)

    def test_invalid_json(self):
        bad_json = "{'a': 1}"  # Single quotes not valid JSON
        res = DevTools.format_json(bad_json)
        self.assertTrue(res.startswith("Error:"))


if __name__ == '__main__':
    unittest.main()
