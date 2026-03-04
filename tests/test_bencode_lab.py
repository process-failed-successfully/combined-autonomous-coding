import unittest
from shared.bencode_lab import BencodeManager


class TestBencodeManager(unittest.TestCase):
    def test_encode_integer(self):
        self.assertEqual(BencodeManager.encode(123), b"i123e")
        self.assertEqual(BencodeManager.encode(-456), b"i-456e")
        self.assertEqual(BencodeManager.encode(0), b"i0e")

    def test_decode_integer(self):
        self.assertEqual(BencodeManager.decode(b"i123e"), 123)
        self.assertEqual(BencodeManager.decode(b"i-456e"), -456)
        self.assertEqual(BencodeManager.decode(b"i0e"), 0)

    def test_encode_string(self):
        self.assertEqual(BencodeManager.encode("spam"), b"4:spam")
        self.assertEqual(BencodeManager.encode(""), b"0:")
        self.assertEqual(BencodeManager.encode(b"hello"), b"5:hello")

    def test_decode_string(self):
        self.assertEqual(BencodeManager.decode(b"4:spam"), b"spam")
        self.assertEqual(BencodeManager.decode(b"0:"), b"")
        self.assertEqual(BencodeManager.decode(b"5:hello"), b"hello")

    def test_encode_list(self):
        self.assertEqual(BencodeManager.encode(["spam", "eggs"]), b"l4:spam4:eggse")
        self.assertEqual(BencodeManager.encode([]), b"le")
        self.assertEqual(BencodeManager.encode([123, "abc"]), b"li123e3:abce")

    def test_decode_list(self):
        self.assertEqual(BencodeManager.decode(b"l4:spam4:eggse"), [b"spam", b"eggs"])
        self.assertEqual(BencodeManager.decode(b"le"), [])
        self.assertEqual(BencodeManager.decode(b"li123e3:abce"), [123, b"abc"])

    def test_encode_dict(self):
        self.assertEqual(BencodeManager.encode({"cow": "moo", "spam": "eggs"}), b"d3:cow3:moo4:spam4:eggse")
        self.assertEqual(BencodeManager.encode({"spam": ["a", "b"]}), b"d4:spaml1:a1:bee")
        self.assertEqual(BencodeManager.encode({}), b"de")

    def test_decode_dict(self):
        self.assertEqual(BencodeManager.decode(b"d3:cow3:moo4:spam4:eggse"), {"cow": b"moo", "spam": b"eggs"})
        self.assertEqual(BencodeManager.decode(b"d4:spaml1:a1:bee"), {"spam": [b"a", b"b"]})
        self.assertEqual(BencodeManager.decode(b"de"), {})

    def test_decode_invalid(self):
        with self.assertRaises(ValueError):
            BencodeManager.decode(b"i123")
        with self.assertRaises(ValueError):
            BencodeManager.decode(b"i-0e")
        with self.assertRaises(ValueError):
            BencodeManager.decode(b"i01e")
        with self.assertRaises(ValueError):
            BencodeManager.decode(b"4:spa")
        with self.assertRaises(ValueError):
            BencodeManager.decode(b"l4:spax")  # missing e
        with self.assertRaises(ValueError):
            BencodeManager.decode(b"di123e3:abce")  # dict key must be string


if __name__ == '__main__':
    unittest.main()
