import unittest
from shared.calc_lab import CalcLabManager

class TestCalcLab(unittest.TestCase):
    def setUp(self):
        self.manager = CalcLabManager()

    def test_basic_arithmetic(self):
        self.assertEqual(self.manager.evaluate("1 + 1"), 2)
        self.assertEqual(self.manager.evaluate("10 - 5"), 5)
        self.assertEqual(self.manager.evaluate("3 * 4"), 12)
        self.assertEqual(self.manager.evaluate("10 / 2"), 5.0)
        self.assertEqual(self.manager.evaluate("10 // 3"), 3)
        self.assertEqual(self.manager.evaluate("10 % 3"), 1)
        self.assertEqual(self.manager.evaluate("2 ** 3"), 8)

    def test_bitwise_operations(self):
        self.assertEqual(self.manager.evaluate("5 & 3"), 1) # 101 & 011 = 001
        self.assertEqual(self.manager.evaluate("5 | 3"), 7) # 101 | 011 = 111
        self.assertEqual(self.manager.evaluate("5 ^ 3"), 6) # 101 ^ 011 = 110 (XOR)
        self.assertEqual(self.manager.evaluate("1 << 2"), 4)
        self.assertEqual(self.manager.evaluate("8 >> 1"), 4)
        self.assertEqual(self.manager.evaluate("~0"), -1)

    def test_hex_bin_oct_input(self):
        self.assertEqual(self.manager.evaluate("0xFF + 1"), 256)
        self.assertEqual(self.manager.evaluate("0b101 + 0b010"), 7)
        self.assertEqual(self.manager.evaluate("0o10"), 8)

    def test_variables(self):
        self.manager.evaluate("x = 10")
        self.assertEqual(self.manager.evaluate("x * 2"), 20)
        self.manager.evaluate("y = x + 5")
        self.assertEqual(self.manager.evaluate("y"), 15)

    def test_math_functions(self):
        self.assertAlmostEqual(self.manager.evaluate("sqrt(16)"), 4.0)
        self.assertAlmostEqual(self.manager.evaluate("sin(0)"), 0.0)
        self.assertAlmostEqual(self.manager.evaluate("cos(0)"), 1.0)
        self.assertAlmostEqual(self.manager.evaluate("min(1, 2, 3)"), 1)
        self.assertAlmostEqual(self.manager.evaluate("max(1, 2, 3)"), 3)
        self.assertAlmostEqual(self.manager.evaluate("abs(-10)"), 10)

    def test_format_result(self):
        res = self.manager.format_result(255)
        self.assertIn("Dec: 255", res)
        self.assertIn("Hex: 0xff", res)
        self.assertIn("Bin: 0b11111111", res)
        self.assertIn("Oct: 0o377", res)

        res_float = self.manager.format_result(3.14)
        self.assertEqual(res_float, "3.14")

    def test_errors(self):
        with self.assertRaises(ValueError):
            self.manager.evaluate("1 / 0")
        with self.assertRaises(ValueError):
            self.manager.evaluate("invalid_syntax +")
        with self.assertRaises(ValueError):
            self.manager.evaluate("unknown_var")

if __name__ == '__main__':
    unittest.main()
