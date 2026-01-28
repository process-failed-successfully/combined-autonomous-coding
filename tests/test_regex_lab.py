import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.regex_lab import RegexLabManager

class TestRegexLabManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = RegexLabManager(self.project_dir)

    def test_match_regex_valid(self):
        pattern = r"\d+"
        text = "abc 123 def 456"
        result = self.manager.match_regex(pattern, text)

        self.assertNotIn("error", result)
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["matches"][0]["group_0"], "123")
        self.assertEqual(result["matches"][1]["group_0"], "456")

    def test_match_regex_no_matches(self):
        pattern = r"\d+"
        text = "abc def"
        result = self.manager.match_regex(pattern, text)

        self.assertNotIn("error", result)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["matches"], [])

    def test_match_regex_invalid_pattern(self):
        pattern = r"["  # Invalid regex
        text = "abc"
        result = self.manager.match_regex(pattern, text)

        self.assertIn("error", result)

    def test_match_regex_flags(self):
        pattern = r"abc"
        text = "ABC"
        # Case sensitive by default
        result = self.manager.match_regex(pattern, text)
        self.assertEqual(result["count"], 0)

        # Ignore case
        result = self.manager.match_regex(pattern, text, flags=re.IGNORECASE)
        self.assertEqual(result["count"], 1)

    @patch("shared.regex_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_explain_regex(self, mock_ask):
        # Mock run_ask_logic to print to stdout (which is captured)
        async def side_effect(*args, **kwargs):
            print("This is an explanation.")
            return True
        mock_ask.side_effect = side_effect

        response = await self.manager.explain_regex(r"\d+")

        self.assertIn("This is an explanation.", response)
        mock_ask.assert_called_once()

    @patch("shared.regex_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_generate_regex(self, mock_ask):
        async def side_effect(*args, **kwargs):
            print("```regex\n\\d+\n```")
            return True
        mock_ask.side_effect = side_effect

        response = await self.manager.generate_regex("Match numbers")

        self.assertIn("\\d+", response)
        mock_ask.assert_called_once()

if __name__ == "__main__":
    unittest.main()
