import unittest
from shared.punycode_lab import punycode_encode, punycode_decode


class TestPunycodeLab(unittest.TestCase):
    def test_encode_ascii(self):
        self.assertEqual(punycode_encode("example.com"), "example.com")

    def test_decode_ascii(self):
        self.assertEqual(punycode_decode("example.com"), "example.com")

    def test_encode_unicode(self):
        self.assertEqual(punycode_encode("münchen.de"), "xn--mnchen-3ya.de")

    def test_decode_unicode(self):
        self.assertEqual(punycode_decode("xn--mnchen-3ya.de"), "münchen.de")

    def test_encode_chinese(self):
        self.assertEqual(punycode_encode("测试.com"), "xn--0zwm56d.com")

    def test_decode_chinese(self):
        self.assertEqual(punycode_decode("xn--0zwm56d.com"), "测试.com")

    def test_encode_invalid(self):
        # Extremely long domain segment
        long_segment = "a" * 100
        with self.assertRaises(ValueError):
            punycode_encode(long_segment + ".com")

    def test_decode_invalid(self):
        # Invalid punycode
        with self.assertRaises(ValueError):
            punycode_decode("xn--invalidpunycode!!!.com")


if __name__ == "__main__":
    unittest.main()
