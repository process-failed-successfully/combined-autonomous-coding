import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.text_lab import TextLabManager

class TestTextLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = TextLabManager()

    def test_transform_basic(self):
        self.assertEqual(self.manager.transform("hello world", "upper"), "HELLO WORLD")
        self.assertEqual(self.manager.transform("HELLO WORLD", "lower"), "hello world")
        self.assertEqual(self.manager.transform("hello world", "title"), "Hello World")
        self.assertEqual(self.manager.transform("hello", "alternating"), "HeLlO")

    def test_transform_cases(self):
        text = "Hello World"
        self.assertEqual(self.manager.transform(text, "camel"), "helloWorld")
        self.assertEqual(self.manager.transform(text, "snake"), "hello_world")
        self.assertEqual(self.manager.transform(text, "kebab"), "hello-world")
        self.assertEqual(self.manager.transform(text, "pascal"), "HelloWorld")
        self.assertEqual(self.manager.transform(text, "constant"), "HELLO_WORLD")

    def test_transform_complex(self):
        text = "foo-bar_baz"
        self.assertEqual(self.manager.transform(text, "camel"), "fooBarBaz")

        text2 = "HTMLParser"
        self.assertEqual(self.manager.transform(text2, "snake"), "html_parser")

    def test_encode_decode_base64(self):
        original = "hello world"
        encoded = self.manager.encode(original, "base64")
        decoded = self.manager.decode(encoded, "base64")
        self.assertEqual(decoded, original)

    def test_encode_decode_url(self):
        original = "hello world/foo"
        encoded = self.manager.encode(original, "url")
        self.assertEqual(encoded, "hello%20world/foo")
        decoded = self.manager.decode(encoded, "url")
        self.assertEqual(decoded, original)

    def test_analyze(self):
        text = "hello world\nhello universe"
        stats = self.manager.analyze(text)
        self.assertEqual(stats['chars'], 26)
        self.assertEqual(stats['lines'], 2)
        self.assertEqual(stats['words'], 4)
        # most common should be hello (2)
        self.assertEqual(stats['most_common'][0][0], "hello")
        self.assertEqual(stats['most_common'][0][1], 2)

    def test_diff(self):
        t1 = "foo\nbar"
        t2 = "foo\nbaz"
        diff = self.manager.diff(t1, t2)
        self.assertIn("-bar", diff)
        self.assertIn("+baz", diff)

if __name__ == '__main__':
    unittest.main()
