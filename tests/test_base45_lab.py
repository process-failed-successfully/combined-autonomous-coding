import unittest
from shared.base45_lab import base45_encode, base45_decode

class TestBase45Lab(unittest.TestCase):
    def test_encode_empty(self):
        self.assertEqual(base45_encode(b""), "")

    def test_decode_empty(self):
        self.assertEqual(base45_decode(""), b"")

    def test_encode_hello(self):
        self.assertEqual(base45_encode(b"Hello!!"), "%69 VD92EX0")

    def test_decode_hello(self):
        self.assertEqual(base45_decode("%69 VD92EX0"), b"Hello!!")

    def test_encode_base_45(self):
        self.assertEqual(base45_encode(b"base-45"), "UJCLQE7W581")

    def test_decode_base_45(self):
        self.assertEqual(base45_decode("UJCLQE7W581"), b"base-45")

    def test_encode_ietf(self):
        self.assertEqual(base45_encode(b"ietf!"), "QED8WEX0")

    def test_decode_ietf(self):
        self.assertEqual(base45_decode("QED8WEX0"), b"ietf!")

if __name__ == "__main__":
    unittest.main()
