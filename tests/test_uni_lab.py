import unittest
from shared.uni_lab import UniLabManager

class TestUniLab(unittest.TestCase):
    def setUp(self):
        self.manager = UniLabManager()

    def test_inspect_ascii(self):
        result = self.manager.inspect("A")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['char'], 'A')
        self.assertEqual(result[0]['code_point'], 'U+0041')
        self.assertEqual(result[0]['name'], 'LATIN CAPITAL LETTER A')

    def test_inspect_emoji(self):
        result = self.manager.inspect("😀")
        self.assertEqual(result[0]['char'], '😀')
        self.assertEqual(result[0]['code_point'], 'U+1F600')
        self.assertIn('GRINNING FACE', result[0]['name'])

    def test_search(self):
        # Limit to 5 to keep test fast, but we need to ensure we find it if we search specific enough
        results = self.manager.search("GRINNING FACE", limit=50)
        self.assertTrue(len(results) > 0)
        found = False
        for res in results:
            if res['code_point'] == 'U+1F600':
                found = True
                break
        self.assertTrue(found)

    def test_escape(self):
        text = "Hello 😀"
        escaped = self.manager.escape(text)
        # \UXXXXXXXX format for wide chars
        self.assertIn("Hello", escaped)
        # python's backslashreplace might output lowercase hex
        self.assertTrue("\\U0001f600" in escaped or "\\U0001F600" in escaped)

    def test_unescape(self):
        text = "Hello \\U0001F600"
        unescaped = self.manager.unescape(text)
        self.assertEqual(unescaped, "Hello 😀")

        text2 = "World \\u0041"
        unescaped2 = self.manager.unescape(text2)
        self.assertEqual(unescaped2, "World A")

if __name__ == '__main__':
    unittest.main()
