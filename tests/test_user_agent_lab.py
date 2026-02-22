import unittest

from shared.user_agent_lab import UserAgentManager


class TestUserAgentManager(unittest.TestCase):
    def setUp(self):
        self.manager = UserAgentManager()

    def test_parse_chrome_windows(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        result = self.manager.parse(ua)
        self.assertEqual(result["browser"], "Chrome")
        self.assertEqual(result["os"], "Windows")
        self.assertEqual(result["version"], "120.0.0.0")
        self.assertEqual(result["engine"], "Blink")
        self.assertEqual(result["is_bot"], "No")

    def test_parse_safari_mac(self):
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        result = self.manager.parse(ua)
        self.assertEqual(result["browser"], "Safari")
        self.assertEqual(result["os"], "Mac OS X")
        self.assertEqual(result["version"], "17.2")
        self.assertEqual(result["engine"], "WebKit")

    def test_parse_bot(self):
        ua = "Googlebot/2.1 (+http://www.google.com/bot.html)"
        result = self.manager.parse(ua)
        self.assertEqual(result["is_bot"], "Yes")

    def test_generate_known(self):
        ua = self.manager.generate("Windows", "Chrome")
        self.assertIsNotNone(ua)
        self.assertIn("Windows", ua)
        self.assertIn("Chrome", ua)

    def test_generate_unknown(self):
        ua = self.manager.generate("UnknownOS", "Browser")
        self.assertIsNone(ua)

    def test_is_bot(self):
        self.assertTrue(self.manager.is_bot("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"))
        self.assertFalse(self.manager.is_bot("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"))


if __name__ == "__main__":
    unittest.main()
