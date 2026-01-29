import unittest
from shared.regex_game import RegexGameEngine, RegexGameLevel

class TestRegexGame(unittest.TestCase):
    def setUp(self):
        self.engine = RegexGameEngine()
        self.level = RegexGameLevel(
            name="Test Level",
            description="Match 'abc'",
            positive_cases=["abc"],
            negative_cases=["ab", "abcd"]
        )

    def test_positive_match(self):
        result = self.engine.validate("abc", self.level)
        self.assertTrue(result["success"])
        self.assertEqual(result["positive_results"], [("abc", True)])
        self.assertEqual(result["negative_results"], [("ab", True), ("abcd", True)])

    def test_negative_match_fails(self):
        # Pattern matches a negative case
        result = self.engine.validate("ab", self.level)
        self.assertFalse(result["success"])
        # "ab" matches "ab" (negative case), so passed=False
        self.assertIn(("ab", False), result["negative_results"])

    def test_positive_miss_fails(self):
        # Pattern fails to match positive case
        result = self.engine.validate("xyz", self.level)
        self.assertFalse(result["success"])
        self.assertIn(("abc", False), result["positive_results"])

    def test_invalid_regex(self):
        result = self.engine.validate("[", self.level)
        self.assertFalse(result["success"])
        self.assertIsNotNone(result["error"])

if __name__ == "__main__":
    unittest.main()
