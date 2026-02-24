import unittest
import re
from shared.regex_lab import RegexLabManager

class TestRegexLabReplace(unittest.TestCase):
    def setUp(self):
        self.manager = RegexLabManager()

    def test_replace_regex_success(self):
        pattern = r"\d+"
        replacement = "NUM"
        text = "abc 123 def 456"
        result = self.manager.replace_regex(pattern, replacement, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["modified_text"], "abc NUM def NUM")

    def test_replace_regex_groups(self):
        pattern = r"(\w+)=(\d+)"
        replacement = r"\2:\1"
        text = "key=123"
        result = self.manager.replace_regex(pattern, replacement, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["modified_text"], "123:key")

    def test_replace_regex_flags(self):
        pattern = r"abc"
        replacement = "XYZ"
        text = "ABC"

        # Without flag
        result = self.manager.replace_regex(pattern, replacement, text)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["modified_text"], "ABC")

        # With flag
        result = self.manager.replace_regex(pattern, replacement, text, flags=re.IGNORECASE)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["modified_text"], "XYZ")

    def test_replace_regex_error(self):
        pattern = r"[" # Invalid regex
        replacement = "foo"
        text = "abc"
        result = self.manager.replace_regex(pattern, replacement, text)

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_replace_regex_no_match(self):
        pattern = r"xyz"
        replacement = "FOO"
        text = "abc"
        result = self.manager.replace_regex(pattern, replacement, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["modified_text"], "abc")

if __name__ == "__main__":
    unittest.main()
