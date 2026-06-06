import unittest
from shared.regex_lab import RegexLabManager
import re

class TestRegexLabExtract(unittest.TestCase):
    def setUp(self):
        self.manager = RegexLabManager()

    def test_extract_regex_basic(self):
        result = self.manager.extract_regex(r"\d+", "123 abc 456 def")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["matches"], ["123", "456"])

    def test_extract_regex_no_match(self):
        result = self.manager.extract_regex(r"\d+", "abc def")
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["matches"], [])

    def test_extract_regex_with_flags(self):
        result = self.manager.extract_regex(r"abc", "ABC def AbC", flags=re.IGNORECASE)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["matches"], ["ABC", "AbC"])

    def test_extract_regex_invalid_pattern(self):
        result = self.manager.extract_regex(r"[unclosed", "text")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()
