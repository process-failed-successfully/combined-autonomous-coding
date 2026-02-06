import unittest
from shared.text_lab import TextLabManager

class TestTextLab(unittest.TestCase):
    def setUp(self):
        self.manager = TextLabManager()

    def test_transform_basic(self):
        self.assertEqual(self.manager.transform("hello", "upper"), "HELLO")
        self.assertEqual(self.manager.transform("HELLO", "lower"), "hello")
        self.assertEqual(self.manager.transform("hello world", "title"), "Hello World")

    def test_transform_cases(self):
        # Camel
        self.assertEqual(self.manager.transform("hello_world", "camel"), "helloWorld")
        self.assertEqual(self.manager.transform("hello-world", "camel"), "helloWorld")
        self.assertEqual(self.manager.transform("Hello World", "camel"), "helloWorld")

        # Snake
        self.assertEqual(self.manager.transform("helloWorld", "snake"), "hello_world")
        self.assertEqual(self.manager.transform("Hello World", "snake"), "hello_world")
        self.assertEqual(self.manager.transform("hello-world", "snake"), "hello_world")

        # Kebab
        self.assertEqual(self.manager.transform("helloWorld", "kebab"), "hello-world")
        self.assertEqual(self.manager.transform("Hello World", "kebab"), "hello-world")
        self.assertEqual(self.manager.transform("hello_world", "kebab"), "hello-world")

        # Pascal
        self.assertEqual(self.manager.transform("hello_world", "pascal"), "HelloWorld")
        self.assertEqual(self.manager.transform("hello-world", "pascal"), "HelloWorld")

        # Constant
        self.assertEqual(self.manager.transform("helloWorld", "constant"), "HELLO_WORLD")

    def test_encode_decode_base64(self):
        original = "hello world"
        encoded = self.manager.encode(original, "base64")
        self.assertEqual(encoded, "aGVsbG8gd29ybGQ=")
        decoded = self.manager.encode(encoded, "base64", decode=True)
        self.assertEqual(decoded, original)

    def test_encode_decode_url(self):
        original = "hello world/?"
        encoded = self.manager.encode(original, "url")
        self.assertEqual(encoded, "hello%20world/%3F")
        decoded = self.manager.encode(encoded, "url", decode=True)
        self.assertEqual(decoded, original)

    def test_encode_decode_html(self):
        original = "<div>&"
        encoded = self.manager.encode(original, "html")
        self.assertEqual(encoded, "&lt;div&gt;&amp;")
        decoded = self.manager.encode(encoded, "html", decode=True)
        self.assertEqual(decoded, original)

    def test_encode_decode_hex(self):
        original = "abc"
        encoded = self.manager.encode(original, "hex")
        self.assertEqual(encoded, "616263")
        decoded = self.manager.encode(encoded, "hex", decode=True)
        self.assertEqual(decoded, original)

    def test_analyze(self):
        text = "hello world\nhello"
        info = self.manager.analyze(text)
        self.assertEqual(info['length'], 17)
        self.assertEqual(info['lines'], 2)
        self.assertEqual(info['words'], 3)
        self.assertEqual(info['chars_no_space'], 15) # 17 - 1 space - 1 newline = 15
        # h:2, e:2, l:5, o:3, w:1, r:1, d:1
        # Top 5 should include l, o, h, e (order might vary for equal counts)
        top_chars = [x[0] for x in info['frequency']]
        self.assertIn('l', top_chars)
        self.assertIn('o', top_chars)

    def test_diff(self):
        t1 = "foo\nbar"
        t2 = "foo\nbaz"
        diff = self.manager.diff(t1, t2)
        self.assertIn("-bar", diff)
        self.assertIn("+baz", diff)

if __name__ == '__main__':
    unittest.main()
