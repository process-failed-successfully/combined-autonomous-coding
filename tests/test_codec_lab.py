import unittest
from shared.codec_lab import CodecLabManager


class TestCodecLabManager(unittest.TestCase):

    def setUp(self):
        self.manager = CodecLabManager()

    def test_base64_encode(self):
        self.assertEqual(self.manager.base64_encode("Hello"), "SGVsbG8=")
        self.assertEqual(self.manager.base64_encode(""), "")

    def test_base64_decode(self):
        self.assertEqual(self.manager.base64_decode("SGVsbG8="), "Hello")
        self.assertEqual(self.manager.base64_decode(""), "")
        self.assertTrue(self.manager.base64_decode("Invalid").startswith("Error:"))

    def test_rot13(self):
        self.assertEqual(self.manager.rot13("Hello"), "Uryyb")
        self.assertEqual(self.manager.rot13("Uryyb"), "Hello")
        self.assertEqual(self.manager.rot13(""), "")

    def test_html_encode(self):
        self.assertEqual(self.manager.html_encode("<a>&b</a>"), "&lt;a&gt;&amp;b&lt;/a&gt;")
        self.assertEqual(self.manager.html_encode(""), "")

    def test_html_decode(self):
        self.assertEqual(self.manager.html_decode("&lt;a&gt;&amp;b&lt;/a&gt;"), "<a>&b</a>")
        self.assertEqual(self.manager.html_decode(""), "")

    def test_url_encode(self):
        self.assertEqual(self.manager.url_encode("Hello World?"), "Hello%20World%3F")
        self.assertEqual(self.manager.url_encode(""), "")

    def test_url_decode(self):
        self.assertEqual(self.manager.url_decode("Hello%20World%3F"), "Hello World?")
        self.assertEqual(self.manager.url_decode(""), "")

    def test_hex_encode(self):
        self.assertEqual(self.manager.hex_encode("Hello"), "48656c6c6f")
        self.assertEqual(self.manager.hex_encode(""), "")

    def test_hex_decode(self):
        self.assertEqual(self.manager.hex_decode("48656c6c6f"), "Hello")
        self.assertEqual(self.manager.hex_decode(""), "")
        self.assertTrue(self.manager.hex_decode("GG").startswith("Error:"))

    def test_binary_encode(self):
        # 'A' is 65 -> 01000001
        self.assertEqual(self.manager.binary_encode("A"), "01000001")
        self.assertEqual(self.manager.binary_encode(""), "")

    def test_binary_decode(self):
        self.assertEqual(self.manager.binary_decode("01000001"), "A")
        self.assertEqual(self.manager.binary_decode(""), "")
        self.assertTrue(self.manager.binary_decode("01").startswith("Error:"))  # Length error
        self.assertTrue(self.manager.binary_decode("00000002").startswith("Error:"))  # Invalid char

    def test_unicode_escape(self):
        self.assertEqual(self.manager.unicode_escape("Hello"), "Hello")
        self.assertEqual(self.manager.unicode_escape("你好"), "\\u4f60\\u597d")
        self.assertEqual(self.manager.unicode_escape(""), "")

    def test_unicode_unescape(self):
        self.assertEqual(self.manager.unicode_unescape("Hello"), "Hello")
        self.assertEqual(self.manager.unicode_unescape("\\u4f60\\u597d"), "你好")
        self.assertEqual(self.manager.unicode_unescape(""), "")
