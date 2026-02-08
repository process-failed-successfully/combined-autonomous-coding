import pytest
from shared.math_lab import MathLabManager
import math

class TestMathLab:
    def setup_method(self):
        self.manager = MathLabManager()

    def test_evaluate_expression_basic(self):
        assert self.manager.evaluate_expression("1 + 1") == 2
        assert self.manager.evaluate_expression("2 * 3 + 4") == 10
        assert self.manager.evaluate_expression("10 / 2") == 5.0
        assert self.manager.evaluate_expression("2 ** 3") == 8
        assert self.manager.evaluate_expression("2 ^ 3") == 8 # XOR as power check

    def test_evaluate_expression_functions(self):
        assert self.manager.evaluate_expression("sqrt(16)") == 4.0
        assert self.manager.evaluate_expression("abs(-5)") == 5
        assert self.manager.evaluate_expression("min(1, 2, 3)") == 1
        assert self.manager.evaluate_expression("max(1, 2, 3)") == 3
        # Rounding issues with float, use pytest.approx
        assert self.manager.evaluate_expression("sin(0)") == pytest.approx(0.0)
        assert self.manager.evaluate_expression("cos(0)") == pytest.approx(1.0)

    def test_evaluate_expression_constants(self):
        assert self.manager.evaluate_expression("pi") == math.pi
        assert self.manager.evaluate_expression("e") == math.e

    def test_evaluate_expression_unsafe(self):
        with pytest.raises(ValueError):
            self.manager.evaluate_expression("__import__('os')")

        with pytest.raises(ValueError):
            self.manager.evaluate_expression("eval('1+1')")

        with pytest.raises(ValueError, match="Unsupported constant type"):
             self.manager.evaluate_expression("'string'")

    def test_calculate_stats(self):
        data = [1, 2, 3, 4, 5]
        stats = self.manager.calculate_stats(data)
        assert stats["count"] == 5
        assert stats["min"] == 1
        assert stats["max"] == 5
        assert stats["sum"] == 15
        assert stats["mean"] == 3
        assert stats["median"] == 3
        # Mode might be anything or None depending on python version for unique set

    def test_calculate_stats_mode(self):
        data = [1, 2, 2, 3]
        stats = self.manager.calculate_stats(data)
        assert stats["mode"] == 2

    def test_is_prime(self):
        assert not self.manager.is_prime(0)
        assert not self.manager.is_prime(1)
        assert self.manager.is_prime(2)
        assert self.manager.is_prime(3)
        assert not self.manager.is_prime(4)
        assert self.manager.is_prime(5)
        assert not self.manager.is_prime(9)
        assert self.manager.is_prime(13)
        assert not self.manager.is_prime(15)
        assert self.manager.is_prime(17)
        assert not self.manager.is_prime(-5)

    def test_generate_primes(self):
        assert self.manager.generate_primes(1, 10) == [2, 3, 5, 7]
        assert self.manager.generate_primes(10, 20) == [11, 13, 17, 19]
