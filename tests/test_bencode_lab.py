import unittest
from shared.bencode_lab import BencodeManager


class TestBencodeLab(unittest.TestCase):
    def setUp(self):
        self.manager = BencodeManager()

    def test_decode_integer(self):
        self.assertEqual(self.manager.decode(b"i42e"), 42)
        self.assertEqual(self.manager.decode(b"i-42e"), -42)

    def test_decode_string(self):
        self.assertEqual(self.manager.decode(b"4:spam"), b"spam")

    def test_decode_list(self):
        self.assertEqual(self.manager.decode(b"l4:spam4:eggse"), [b"spam", b"eggs"])

    def test_decode_dict(self):
        self.assertEqual(
            self.manager.decode(b"d3:cow3:moo4:spam4:eggse"),
            {"cow": b"moo", "spam": b"eggs"}
        )

    def test_encode_integer(self):
        self.assertEqual(self.manager.encode(42), b"i42e")
        self.assertEqual(self.manager.encode(-42), b"i-42e")

    def test_encode_string(self):
        self.assertEqual(self.manager.encode("spam"), b"4:spam")
        self.assertEqual(self.manager.encode(b"spam"), b"4:spam")

    def test_encode_list(self):
        self.assertEqual(self.manager.encode(["spam", "eggs"]), b"l4:spam4:eggse")

    def test_encode_dict(self):
        self.assertEqual(
            self.manager.encode({"cow": "moo", "spam": "eggs"}),
            b"d3:cow3:moo4:spam4:eggse"
        )

    def test_encode_decode_roundtrip(self):
        original = {"tracker": "http://tracker.com", "info": {"piece length": 262144, "name": "test"}}
        encoded = self.manager.encode(original)
        decoded = self.manager.decode(encoded)

        json_ready = self.manager.json_ready(decoded)
        self.assertEqual(json_ready, original)

    def test_invalid_decode(self):
        with self.assertRaises(ValueError):
            self.manager.decode(b"i42")  # missing 'e'
        with self.assertRaises(ValueError):
            self.manager.decode(b"5:spam")  # length mismatch


if __name__ == "__main__":
    unittest.main()
