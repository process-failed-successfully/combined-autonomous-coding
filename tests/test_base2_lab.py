import unittest
from shared.base2_lab import encode_base2, decode_base2


class TestBase2Lab(unittest.TestCase):
    def test_encode_base2(self):
        self.assertEqual(encode_base2("A"), "01000001")
        self.assertEqual(encode_base2("Hello"), "01001000 01100101 01101100 01101100 01101111")

    def test_decode_base2(self):
        # Spaced binary
        self.assertEqual(decode_base2("01000001"), "A")
        self.assertEqual(decode_base2("01001000 01100101 01101100 01101100 01101111"), "Hello")

        # Continuous binary
        self.assertEqual(decode_base2("0100100001100101011011000110110001101111"), "Hello")

    def test_decode_base2_invalid_length(self):
        with self.assertRaises(ValueError) as ctx:
            decode_base2("0100000")
        self.assertIn("multiple of 8", str(ctx.exception))

    def test_decode_base2_invalid_characters(self):
        with self.assertRaises(ValueError) as ctx:
            decode_base2("01000002")
        self.assertIn("Invalid characters", str(ctx.exception))

    def test_encode_decode_emoji(self):
        emoji_str = "🌟"
        encoded = encode_base2(emoji_str)
        decoded = decode_base2(encoded)
        self.assertEqual(decoded, emoji_str)


if __name__ == "__main__":
    unittest.main()
