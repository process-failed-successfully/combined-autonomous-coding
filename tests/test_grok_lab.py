import unittest
from unittest.mock import MagicMock
from shared.grok_lab import GrokManager

class TestGrokLab(unittest.TestCase):
    def setUp(self):
        self.manager = GrokManager()

    def test_grok_parse_success(self):
        pattern = "%{IP:client} %{WORD:method} %{URIPATHPARAM:request} %{NUMBER:bytes}"
        text = "10.0.0.1 GET /index.html 15824"
        result = self.manager.parse(pattern, text)

        self.assertTrue(result["success"])
        self.assertEqual(result["match"]["client"], "10.0.0.1")
        self.assertEqual(result["match"]["method"], "GET")
        self.assertEqual(result["match"]["request"], "/index.html")
        self.assertEqual(result["match"]["bytes"], "15824")

    def test_grok_parse_no_match(self):
        pattern = "%{IP:client}"
        text = "not_an_ip"
        result = self.manager.parse(pattern, text)

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Pattern did not match the input text.")

    def test_grok_parse_invalid_pattern(self):
        # A totally bogus pattern that doesn't exist
        pattern = "%{BOGUS_PATTERN:bogus}"
        text = "some text"
        result = self.manager.parse(pattern, text)

        # pygrok might fail or simply not match.
        # usually bogus pattern causes a match failure or compile exception
        self.assertFalse(result["success"])

    def test_get_patterns(self):
        patterns = self.manager.get_patterns()
        self.assertIn("IP", patterns)
        self.assertIn("WORD", patterns)
        self.assertIn("NUMBER", patterns)

    def test_tui_initialization(self):
        try:
            from shared.tui_grok import GrokLabTab
            tab = GrokLabTab()
            self.assertEqual(tab.id, "tab-grok")
        except Exception as e:
            self.fail(f"TUI initialization failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()
