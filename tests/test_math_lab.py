import unittest
from unittest.mock import MagicMock, patch
import math
import sys
from io import StringIO
from shared.math_lab import MathLabManager, run_math_lab_logic

class TestMathLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MathLabManager()

    def test_evaluate_basic(self):
        self.assertEqual(self.manager.evaluate("1 + 1"), 2)
        self.assertEqual(self.manager.evaluate("2 * 3"), 6)
        self.assertEqual(self.manager.evaluate("10 / 2"), 5)
        self.assertEqual(self.manager.evaluate("10 - 2"), 8)
        self.assertEqual(self.manager.evaluate("2 ** 3"), 8)
        self.assertEqual(self.manager.evaluate("2 ^ 3"), 8) # Custom ^ support
        self.assertEqual(self.manager.evaluate("10 % 3"), 1)

    def test_evaluate_constants(self):
        self.assertAlmostEqual(self.manager.evaluate("pi"), math.pi)
        self.assertAlmostEqual(self.manager.evaluate("e"), math.e)

    def test_evaluate_functions(self):
        self.assertAlmostEqual(self.manager.evaluate("sin(0)"), 0)
        self.assertAlmostEqual(self.manager.evaluate("cos(0)"), 1)
        self.assertEqual(self.manager.evaluate("sqrt(4)"), 2)
        self.assertEqual(self.manager.evaluate("abs(-5)"), 5)
        self.assertEqual(self.manager.evaluate("max(1, 2)"), 2)
        self.assertEqual(self.manager.evaluate("min(1, 2)"), 1)

    def test_evaluate_complex(self):
        self.assertEqual(self.manager.evaluate("2 * (3 + 4)"), 14)
        self.assertAlmostEqual(self.manager.evaluate("sin(pi/2)"), 1)

    def test_evaluate_errors(self):
        self.assertTrue(str(self.manager.evaluate("1 / 0")).startswith("Error: Division by zero"))
        self.assertTrue(str(self.manager.evaluate("unknown_func(1)")).startswith("Error"))
        self.assertTrue(str(self.manager.evaluate("x + 1")).startswith("Error")) # Unknown variable
        self.assertTrue(str(self.manager.evaluate("__import__('os')")).startswith("Error")) # Unsafe

    def test_statistics(self):
        numbers = [1, 2, 3, 4, 5]
        stats = self.manager.statistics(numbers)
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["sum"], 15)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3)
        self.assertEqual(stats["median"], 3)
        self.assertEqual(stats["stdev"], 1.5811388300841898)

    def test_statistics_empty(self):
        self.assertEqual(self.manager.statistics([]), {"error": "No numbers provided"})

    def test_prime_info(self):
        info_2 = self.manager.prime_info(2)
        self.assertTrue(info_2["is_prime"])
        self.assertEqual(info_2["next_prime"], 3)
        self.assertIsNone(info_2["prev_prime"])
        self.assertEqual(info_2["factors"], [1, 2])

        info_10 = self.manager.prime_info(10)
        self.assertFalse(info_10["is_prime"])
        self.assertEqual(info_10["next_prime"], 11)
        self.assertEqual(info_10["prev_prime"], 7)
        self.assertEqual(info_10["factors"], [1, 2, 5, 10])

        info_17 = self.manager.prime_info(17)
        self.assertTrue(info_17["is_prime"])

    def test_is_prime(self):
        self.assertFalse(self.manager.is_prime(1))
        self.assertTrue(self.manager.is_prime(2))
        self.assertTrue(self.manager.is_prime(3))
        self.assertFalse(self.manager.is_prime(4))
        self.assertTrue(self.manager.is_prime(5))
        self.assertFalse(self.manager.is_prime(6))
        self.assertTrue(self.manager.is_prime(7))
        self.assertFalse(self.manager.is_prime(9))
        self.assertFalse(self.manager.is_prime(15))
        self.assertTrue(self.manager.is_prime(19))

class TestRunMathLabLogic(unittest.TestCase):
    def test_eval_action(self):
        args = MagicMock()
        args.action = "eval"
        args.expression = "1 + 1"

        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_math_lab_logic(args)
            self.assertTrue(success)
            self.assertEqual(fake_out.getvalue().strip(), "2")

    def test_stats_action(self):
        args = MagicMock()
        args.action = "stats"
        args.numbers = ["1", "2", "3"]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_math_lab_logic(args)
            self.assertTrue(success)
            output = fake_out.getvalue()
            self.assertIn("Mean", output)
            self.assertIn("3.0000", output) # Sum is 6, mean is 2. Wait, logic test says 3. Mean of 1,2,3 is 2.

    def test_prime_action(self):
        args = MagicMock()
        args.action = "prime"
        args.n = 5

        with patch('sys.stdout', new=StringIO()) as fake_out:
            success = run_math_lab_logic(args)
            self.assertTrue(success)
            output = fake_out.getvalue()
            self.assertIn("Is Prime:   True", output)
            self.assertIn("Next Prime: 7", output)

if __name__ == '__main__':
    unittest.main()
