import unittest
import re
from unittest.mock import patch, AsyncMock
from pathlib import Path
from shared.regex_lab import RegexLabManager

class TestRegexLab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = RegexLabManager()
        self.project_dir = Path("/tmp/test_project")

    def test_match_regex_success(self):
        pattern = r"\d+"
        text = "abc 123 def 456"
        result = self.manager.match_regex(pattern, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["matches"][0]["full_match"], "123")
        self.assertEqual(result["matches"][1]["full_match"], "456")

    def test_match_regex_groups(self):
        pattern = r"(\w+)=(\d+)"
        text = "key=123"
        result = self.manager.match_regex(pattern, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["matches"][0]["groups"], ("key", "123"))

    def test_match_regex_named_groups(self):
        pattern = r"(?P<name>\w+)=(?P<val>\d+)"
        text = "foo=42"
        result = self.manager.match_regex(pattern, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["matches"][0]["group_dict"], {"name": "foo", "val": "42"})

    def test_match_regex_flags(self):
        pattern = r"abc"
        text = "ABC"
        # Without flag
        result = self.manager.match_regex(pattern, text)
        self.assertEqual(result["count"], 0)

        # With flag
        result = self.manager.match_regex(pattern, text, flags=re.IGNORECASE)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)

    def test_match_regex_error(self):
        pattern = r"[" # Invalid regex
        text = "abc"
        result = self.manager.match_regex(pattern, text)

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("shared.regex_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_explain_regex(self, mock_ask):
        mock_ask.return_value = True

        success = await self.manager.explain_regex(
            pattern="^test$",
            project_dir=self.project_dir,
            agent_type="gemini"
        )

        self.assertTrue(success)
        mock_ask.assert_called_once()
        call_args = mock_ask.call_args[1]
        self.assertIn("^test$", call_args["query"])
        self.assertEqual(call_args["project_dir"], self.project_dir)

    @patch("shared.regex_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_generate_regex(self, mock_ask):
        mock_ask.return_value = True

        success = await self.manager.generate_regex(
            description="email address",
            project_dir=self.project_dir,
            agent_type="gemini"
        )

        self.assertTrue(success)
        mock_ask.assert_called_once()
        call_args = mock_ask.call_args[1]
        self.assertIn("email address", call_args["query"])

if __name__ == "__main__":
    unittest.main()
