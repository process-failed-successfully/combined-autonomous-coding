import unittest
from shared.bitwise_lab import BitwiseLabManager


class TestBitwiseLab(unittest.TestCase):
    def setUp(self):
        self.manager = BitwiseLabManager()

    def test_parse_value(self):
        self.assertEqual(self.manager.parse_value("255"), 255)
        self.assertEqual(self.manager.parse_value("0xFF"), 255)
        self.assertEqual(self.manager.parse_value("0b11111111"), 255)
        self.assertEqual(self.manager.parse_value("0o377"), 255)
        with self.assertRaises(ValueError):
            self.manager.parse_value("invalid")

    def test_format_value(self):
        fmt = self.manager.format_value(255, 32)
        self.assertEqual(fmt["dec_unsigned"], "255")
        self.assertEqual(fmt["dec_signed"], "255")
        self.assertEqual(fmt["hex"], "0x000000FF")
        self.assertEqual(fmt["bin"], "0b00000000000000000000000011111111")
        self.assertEqual(fmt["oct"], "0o377")

        # Test negative representation within 8 bits
        fmt_neg = self.manager.format_value(-1, 8)
        self.assertEqual(fmt_neg["dec_unsigned"], "255")
        self.assertEqual(fmt_neg["dec_signed"], "-1")
        self.assertEqual(fmt_neg["hex"], "0xFF")
        self.assertEqual(fmt_neg["bin"], "0b11111111")

    def test_bitwise_and(self):
        self.assertEqual(self.manager.bitwise_and(0b1100, 0b1010, 8), 0b1000)

    def test_bitwise_or(self):
        self.assertEqual(self.manager.bitwise_or(0b1100, 0b1010, 8), 0b1110)

    def test_bitwise_xor(self):
        self.assertEqual(self.manager.bitwise_xor(0b1100, 0b1010, 8), 0b0110)

    def test_bitwise_not(self):
        # NOT 0 in 8-bit is 255
        self.assertEqual(self.manager.bitwise_not(0, 8), 255)

    def test_bitwise_lshift(self):
        self.assertEqual(self.manager.bitwise_lshift(1, 2, 8), 4)
        # Shift out of bounds (8-bit)
        self.assertEqual(self.manager.bitwise_lshift(0b10000000, 1, 8), 0)

    def test_bitwise_rshift(self):
        self.assertEqual(self.manager.bitwise_rshift(4, 1, 8), 2)
        # Verify it's a logical right shift (no sign extension on negative values)
        # -1 (255 in 8-bit) >> 1 = 127
        self.assertEqual(self.manager.bitwise_rshift(-1, 1, 8), 127)

    def test_swap_bytes(self):
        # 16 bit: 0x1234 -> 0x3412
        self.assertEqual(self.manager.swap_bytes(0x1234, 16), 0x3412)
        # 32 bit: 0x12345678 -> 0x78563412
        self.assertEqual(self.manager.swap_bytes(0x12345678, 32), 0x78563412)
        with self.assertRaises(ValueError):
            self.manager.swap_bytes(0x12, 8)


if __name__ == '__main__':
    unittest.main()
