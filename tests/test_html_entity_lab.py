import unittest
from shared.html_entity_lab import HtmlEntityLabManager

class TestHtmlEntityLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = HtmlEntityLabManager()

    def test_encode(self):
        # Basic tags
        self.assertEqual(self.manager.encode("<test>"), "&lt;test&gt;")

        # Quotes and ampersands
        self.assertEqual(self.manager.encode("AT&T 'and' \"friends\""), "AT&amp;T &#x27;and&#x27; &quot;friends&quot;")

        # Empty string
        self.assertEqual(self.manager.encode(""), "")

        # No special chars
        self.assertEqual(self.manager.encode("hello world"), "hello world")

    def test_decode(self):
        # Basic entities
        self.assertEqual(self.manager.decode("&lt;test&gt;"), "<test>")

        # Mixed entities
        self.assertEqual(self.manager.decode("AT&amp;T &#x27;and&#x27; &quot;friends&quot;"), "AT&T 'and' \"friends\"")

        # Empty string
        self.assertEqual(self.manager.decode(""), "")

        # Unescaped string
        self.assertEqual(self.manager.decode("hello world"), "hello world")

if __name__ == "__main__":
    unittest.main()
