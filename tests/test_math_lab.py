import unittest
from unittest.mock import MagicMock
from shared.math_lab import MathLabManager, run_math_lab_logic
import math
import sys
from io import StringIO

class TestMathLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = MathLabManager()

    def test_evaluate_basic(self):
        self.assertEqual(self.manager.evaluate("1 + 2"), 3)
        self.assertEqual(self.manager.evaluate("2 * 3 + 4"), 10)
        self.assertEqual(self.manager.evaluate("10 / 2"), 5.0)
        self.assertEqual(self.manager.evaluate("2 ^ 3"), 8)
        self.assertEqual(self.manager.evaluate("2 ** 3"), 8)

    def test_evaluate_functions(self):
        self.assertAlmostEqual(self.manager.evaluate("sin(0)"), 0.0)
        self.assertAlmostEqual(self.manager.evaluate("cos(0)"), 1.0)
        self.assertAlmostEqual(self.manager.evaluate("sqrt(4)"), 2.0)
        self.assertEqual(self.manager.evaluate("abs(-5)"), 5)
        self.assertEqual(self.manager.evaluate("min(1, 2, 3)"), 1)
        self.assertEqual(self.manager.evaluate("max(1, 2, 3)"), 3)

    def test_evaluate_constants(self):
        self.assertAlmostEqual(self.manager.evaluate("pi"), math.pi)
        self.assertAlmostEqual(self.manager.evaluate("e"), math.e)

    def test_evaluate_errors(self):
        with self.assertRaises(ValueError):
            self.manager.evaluate("print('hello')") # Unsafe
        with self.assertRaises(ValueError):
            self.manager.evaluate("__import__('os')") # Unsafe
        with self.assertRaises(ValueError):
            self.manager.evaluate("1 / 0") # Division by zero
        with self.assertRaises(ValueError):
            self.manager.evaluate("unknown_func(1)")

    def test_evaluate_non_numeric_function(self):
        # Mock a function that returns a string
        self.manager.allowed_names["str_func"] = lambda x: "string"
        with self.assertRaises(ValueError) as cm:
            self.manager.evaluate("str_func(1)")
        self.assertIn("returned non-numeric value", str(cm.exception))

    def test_stats_basic(self):
        numbers = [1, 2, 3, 4, 5]
        stats = self.manager.calculate_stats(numbers)
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3.0)
        self.assertEqual(stats["median"], 3.0)

    def test_stats_empty(self):
        self.assertEqual(self.manager.calculate_stats([]), {})

    def test_primes(self):
        # Is Prime
        self.assertTrue(self.manager.is_prime(2))
        self.assertTrue(self.manager.is_prime(3))
        self.assertTrue(self.manager.is_prime(17))
        self.assertFalse(self.manager.is_prime(1))
        self.assertFalse(self.manager.is_prime(4))
        self.assertFalse(self.manager.is_prime(15))

        # Next Prime
        self.assertEqual(self.manager.next_prime(1), 2)
        self.assertEqual(self.manager.next_prime(2), 3)
        self.assertEqual(self.manager.next_prime(14), 17)

        # Prime Factors
        self.assertEqual(self.manager.prime_factors(12), [2, 2, 3])
        self.assertEqual(self.manager.prime_factors(17), [17])
        self.assertEqual(self.manager.prime_factors(1), [])


class TestMathLabCLI(unittest.TestCase):
    def test_eval_cli(self):
        args = MagicMock()
        args.action = "eval"
        args.expression = "1+1"

        # Capture stdout
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            run_math_lab_logic(args)
            output = out.getvalue().strip()
            self.assertEqual(output, "2")
        finally:
            sys.stdout = saved_stdout

    def test_stats_cli(self):
        args = MagicMock()
        args.action = "stats"
        args.numbers = ["1", "2", "3"]

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            run_math_lab_logic(args)
            output = out.getvalue().strip()
            self.assertIn("Count: 3", output)
            self.assertIn("Mean: 2.0000", output)
        finally:
            sys.stdout = saved_stdout

    def test_prime_cli(self):
        args = MagicMock()
        args.action = "prime"
        args.subaction = "check"
        args.number = "7"

        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            run_math_lab_logic(args)
            output = out.getvalue().strip()
            self.assertIn("7 is prime", output)
        finally:
            sys.stdout = saved_stdout

if __name__ == '__main__':
    unittest.main()
