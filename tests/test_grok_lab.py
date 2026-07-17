import unittest
from shared.grok_lab import GrokManager


class TestGrokManager(unittest.TestCase):
    def setUp(self):
        self.manager = GrokManager()

    def test_parse_simple_word(self):
        pattern = "%{WORD:my_word}"
        text = "Hello world"
        result = self.manager.parse(pattern, text)
        self.assertEqual(result, {"my_word": "Hello"})

    def test_parse_multiple_fields(self):
        pattern = "%{IPV4:ip} %{WORD:verb} %{INT:status}"
        text = "192.168.1.1 GET 200"
        result = self.manager.parse(pattern, text)
        self.assertEqual(result, {"ip": "192.168.1.1", "verb": "GET", "status": "200"})

    def test_parse_no_match(self):
        pattern = "%{IPV4:ip}"
        text = "not_an_ip"
        result = self.manager.parse(pattern, text)
        self.assertEqual(result, {})

    def test_parse_invalid_pattern(self):
        with self.assertRaises(ValueError):
            self.manager.parse("%{NONEXISTENT_PATTERN:var}", "text")

    def test_custom_pattern(self):
        self.manager.add_pattern("CUSTOM", r"[A-Z]{3}")
        result = self.manager.parse("%{CUSTOM:code}", "ABC")
        self.assertEqual(result, {"code": "ABC"})


if __name__ == '__main__':
    unittest.main()
