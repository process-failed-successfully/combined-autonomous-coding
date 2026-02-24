import unittest
import json
from shared.pipeline_lab import PipelineLabManager

class TestPipelineLab(unittest.TestCase):
    def setUp(self):
        self.manager = PipelineLabManager()

    def test_text_ops(self):
        self.assertEqual(self.manager.process("hello", ["upper"]), "HELLO")
        self.assertEqual(self.manager.process("HELLO", ["lower"]), "hello")
        self.assertEqual(self.manager.process("hello", ["reverse"]), "olleh")
        self.assertEqual(self.manager.process("  hello  ", ["strip"]), "hello")

    def test_encoding_ops(self):
        # Base64
        encoded = self.manager.process("hello", ["base64-encode"])
        self.assertEqual(encoded, "aGVsbG8=")
        decoded = self.manager.process(encoded, ["base64-decode"])
        self.assertEqual(decoded, "hello")

        # Hex
        hex_enc = self.manager.process("hello", ["hex-encode"])
        self.assertEqual(hex_enc, "68656c6c6f")
        hex_dec = self.manager.process(hex_enc, ["hex-decode"])
        self.assertEqual(hex_dec, "hello")

        # URL
        url_enc = self.manager.process("hello world", ["url-encode"])
        self.assertEqual(url_enc, "hello%20world")
        url_dec = self.manager.process(url_enc, ["url-decode"])
        self.assertEqual(url_dec, "hello world")

    def test_json_ops(self):
        json_str = '{"name": "test", "items": [1, 2, 3]}'

        # Parse and Get
        val = self.manager.process(json_str, ["json-parse", "json-get name"])
        self.assertEqual(val, "test")

        # Get nested
        val = self.manager.process(json_str, ["json-parse", "json-get items.1"])
        self.assertEqual(val, 2)

        # Stringify
        obj = {"a": 1}
        s = self.manager.process(obj, ["json-stringify"])
        self.assertIn('"a": 1', s)

    def test_list_ops(self):
        data = "a,b,c,a"

        # Split
        res = self.manager.process(data, ["split ,"])
        self.assertEqual(res, ["a", "b", "c", "a"])

        # Unique & Sort
        res = self.manager.process(data, ["split ,", "unique", "sort"])
        self.assertEqual(res, ["a", "b", "c"])

        # Count
        res = self.manager.process(data, ["split ,", "count"])
        self.assertEqual(res, 4)

        # Slice
        res = self.manager.process("1,2,3,4,5", ["split ,", "slice 1:4"])
        self.assertEqual(res, ["2", "3", "4"])

    def test_map_op(self):
        data = "a,b,c"
        # map upper
        res = self.manager.process(data, ["split ,", "map upper"])
        self.assertEqual(res, ["A", "B", "C"])

        # map chaining
        # "1,2,3" -> ["1", "2", "3"] -> map (lambda x: int(x) is hard via string ops)
        # but let's try something else: map reverse
        data = "abc,def"
        res = self.manager.process(data, ["split ,", "map reverse"])
        self.assertEqual(res, ["cba", "fed"])

    def test_filter_ops(self):
        data = "apple\nbanana\ncherry\ndate"
        res = self.manager.process(data, ["lines", "grep a"])
        self.assertEqual(res, ["apple", "banana", "date"])

        res = self.manager.process(data, ["lines", "exclude a"])
        self.assertEqual(res, ["cherry"])

    def test_math_ops(self):
        # We need a list of numbers.
        # Since 'split' produces strings, 'sum' on strings concatenates them or fails if sum expects numbers.
        # Python sum(strings) raises TypeError.
        # We don't have a 'to-int' op easily available for map unless we add it or use eval (unsafe).
        # But we can test math ops by passing raw list if we were calling python directly,
        # but via process string ops...
        # Wait, I didn't implement 'int' or 'float' conversion ops.
        # Let's add them to test pipeline or just test directly.
        # But 'json-parse' can return numbers!

        json_data = "[1, 2, 3, 4]"
        res = self.manager.process(json_data, ["json-parse", "sum"])
        self.assertEqual(res, 10)

        res = self.manager.process(json_data, ["json-parse", "max"])
        self.assertEqual(res, 4)

        res = self.manager.process(json_data, ["json-parse", "avg"])
        self.assertEqual(res, 2.5)

    def test_error_handling(self):
        with self.assertRaises(ValueError):
            self.manager.process("test", ["unknown-op"])

        with self.assertRaises(ValueError):
            # Invalid JSON
            self.manager.process("{invalid", ["json-parse"])

if __name__ == '__main__':
    unittest.main()
