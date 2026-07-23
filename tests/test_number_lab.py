import unittest
from shared.number_lab import NumberLabManager

class TestNumberLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = NumberLabManager()

    def test_parse(self):
        self.assertEqual(self.manager.parse("123"), 123)
        self.assertEqual(self.manager.parse("0xFF"), 255)
        self.assertEqual(self.manager.parse("0b1010"), 10)
        self.assertEqual(self.manager.parse("0o10"), 8)
        self.assertEqual(self.manager.parse("3.14"), 3.14)
        with self.assertRaises(ValueError):
            self.manager.parse("abc")

    def test_convert(self):
        self.assertEqual(self.manager.convert("10", 2), "0b1010")
        self.assertEqual(self.manager.convert("10", 8), "0o12")
        self.assertEqual(self.manager.convert("0xFF", 10), "255")
        self.assertEqual(self.manager.convert("255", 16), "0xff")
        with self.assertRaises(ValueError):
            self.manager.convert("3.14", 2)
        with self.assertRaises(ValueError):
            self.manager.convert("10", 3)

    def test_is_prime(self):
        self.assertTrue(self.manager.is_prime("2"))
        self.assertTrue(self.manager.is_prime("17"))
        self.assertTrue(self.manager.is_prime("97"))
        self.assertFalse(self.manager.is_prime("1"))
        self.assertFalse(self.manager.is_prime("0"))
        self.assertFalse(self.manager.is_prime("-5"))
        self.assertFalse(self.manager.is_prime("100"))
        self.assertFalse(self.manager.is_prime("3.14"))
        self.assertTrue(self.manager.is_prime("17.0"))

    def test_factors(self):
        self.assertEqual(self.manager.factors("100"), [2, 2, 5, 5])
        self.assertEqual(self.manager.factors("17"), [17])
        self.assertEqual(self.manager.factors("1"), [])
        self.assertEqual(self.manager.factors("-5"), [])
        self.assertEqual(self.manager.factors("12"), [2, 2, 3])
        with self.assertRaises(ValueError):
            self.manager.factors("3.14")

    def test_stats(self):
        stats = self.manager.stats(["1", "2", "3", "4", "5"])
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["sum"], 15)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3)
        self.assertEqual(stats["median"], 3)
        self.assertEqual(stats["variance"], 2.5)

        with self.assertRaises(ValueError):
            self.manager.stats([])

if __name__ == '__main__':
    unittest.main()
