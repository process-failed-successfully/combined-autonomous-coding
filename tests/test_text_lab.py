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

    def test_new_case_transforms(self):
        # Dot
        self.assertEqual(self.manager.transform("hello_world", "dot"), "hello.world")
        self.assertEqual(self.manager.transform("Hello World", "dot"), "hello.world")

        # Path
        self.assertEqual(self.manager.transform("hello_world", "path"), "hello/world")
        self.assertEqual(self.manager.transform("Hello World", "path"), "hello/world")

    def test_line_operations(self):
        # Sort
        text = "c\na\nb"
        self.assertEqual(self.manager.sort_lines(text), "a\nb\nc")
        self.assertEqual(self.manager.sort_lines(text, reverse=True), "c\nb\na")

        # Unique
        text = "a\nb\na"
        self.assertEqual(self.manager.unique_lines(text), "a\nb")

        # Reverse
        text = "a\nb\nc"
        self.assertEqual(self.manager.reverse_lines(text), "c\nb\na")

        # Shuffle (just check length and content preservation)
        text = "a\nb\nc"
        shuffled = self.manager.shuffle_lines(text)
        self.assertEqual(len(shuffled), len(text))
        self.assertIn("a", shuffled)
        self.assertIn("b", shuffled)
        self.assertIn("c", shuffled)

        # Number
        text = "foo\nbar"
        self.assertEqual(self.manager.number_lines(text), "1. foo\n2. bar")

    def test_whitespace_operations(self):
        # Trim
        text = "  foo  \n  bar  "
        self.assertEqual(self.manager.trim_lines(text), "foo\nbar")

        # Remove Empty
        text = "foo\n\nbar\n   "
        self.assertEqual(self.manager.remove_empty_lines(text), "foo\nbar")

        # Collapse Spaces
        text = "foo    bar   baz"
        self.assertEqual(self.manager.collapse_spaces(text), "foo bar baz")

    def test_filter_lines(self):
        text = "apple\nbanana\ncherry"

        # Include
        self.assertEqual(self.manager.filter_lines(text, "a"), "apple\nbanana")
        self.assertEqual(self.manager.filter_lines(text, "cherry"), "cherry")

        # Exclude
        self.assertEqual(self.manager.filter_lines(text, "a", exclude=True), "cherry")

        # Invalid Regex
        self.assertTrue(self.manager.filter_lines(text, "[").startswith("Error:"))

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
        self.assertEqual(info['chars_no_space'], 15)  # 17 - 1 space - 1 newline = 15
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

    def test_hash_text(self):
        text = "hello"
        md5_hash = self.manager.hash_text(text, "md5")
        sha1_hash = self.manager.hash_text(text, "sha1")
        sha256_hash = self.manager.hash_text(text, "sha256")
        sha512_hash = self.manager.hash_text(text, "sha512")

        self.assertEqual(md5_hash, "5d41402abc4b2a76b9719d911017c592")
        self.assertEqual(sha1_hash, "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d")
        self.assertEqual(sha256_hash, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
        self.assertEqual(sha512_hash, "9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043")

        with self.assertRaises(ValueError):
            self.manager.hash_text(text, "unknown_algo")


if __name__ == '__main__':
    unittest.main()
