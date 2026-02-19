import ast
import math
import statistics
import sys
from typing import Dict, List, Optional, Sequence, Union


class MathLabManager:
    """Manages Math Lab operations: evaluate, stats, and primes."""

    def __init__(self):
        self.allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        self.allowed_names.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        })

    def _safe_eval(self, node: ast.AST) -> Union[int, float]:
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant):  # Python >= 3.8
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Constant type {type(node.value)} not allowed")
        elif isinstance(node, ast.BinOp):
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ValueError("Division by zero")
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0:
                    raise ValueError("Division by zero")
                return left // right
            elif isinstance(node.op, ast.Mod):
                return left % right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            elif isinstance(node.op, ast.BitXor):  # Using ^ for power as well, common in calculators
                return left ** right
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.allowed_names:
                    args = [self._safe_eval(arg) for arg in node.args]
                    return self.allowed_names[func_name](*args)
                else:
                    raise ValueError(f"Function '{func_name}' not allowed")
        elif isinstance(node, ast.Name):
            if node.id in self.allowed_names:
                return self.allowed_names[node.id]
            raise ValueError(f"Variable '{node.id}' not allowed")

        raise ValueError(f"Unsupported operation: {type(node).__name__}")

    def evaluate(self, expression: str) -> Union[float, int]:
        """Safely evaluates a mathematical expression."""
        if not expression:
            raise ValueError("Empty expression")

        # Replace ^ with ** for power if users use ^
        # But wait, ^ is BitXor in Python. I handled BitXor in _safe_eval to behave like Pow.

        try:
            tree = ast.parse(expression, mode='eval')
            return self._safe_eval(tree)
        except SyntaxError as e:
            raise ValueError(f"Invalid syntax: {e}")
        except Exception as e:
            raise ValueError(str(e))

    def calculate_stats(self, numbers: Sequence[float]) -> Dict[str, Optional[Union[float, int]]]:
        """Calculates basic statistics for a list of numbers."""
        if not numbers:
            return {}

        result: Dict[str, Optional[Union[float, int]]] = {
            "count": len(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "sum": sum(numbers),
            "mean": statistics.mean(numbers),
            "median": statistics.median(numbers),
        }

        try:
            result["mode"] = statistics.mode(numbers)
        except statistics.StatisticsError:
            result["mode"] = None  # No unique mode

        if len(numbers) > 1:
            result["stdev"] = statistics.stdev(numbers)
            result["variance"] = statistics.variance(numbers)
        else:
            result["stdev"] = 0.0
            result["variance"] = 0.0

        return result

    def is_prime(self, n: int) -> bool:
        """Checks if a number is prime."""
        if n <= 1:
            return False
        if n <= 3:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    def next_prime(self, n: int) -> int:
        """Finds the next prime number strictly greater than n."""
        if n < 2:
            return 2
        candidate = n + 1
        while True:
            if self.is_prime(candidate):
                return candidate
            candidate += 1

    def prime_factors(self, n: int) -> List[int]:
        """Returns the prime factorization of n."""
        factors = []
        d = 2
        temp = n
        while d * d <= temp:
            while temp % d == 0:
                factors.append(d)
                temp //= d
            d += 1
        if temp > 1:
            factors.append(temp)
        return factors


def run_math_lab_logic(args) -> bool:
    """CLI handler for Math Lab."""
    manager = MathLabManager()

    if args.action == "eval":
        expr = args.expression
        if not expr:
            # Try to read from stdin if not provided
            if not sys.stdin.isatty():
                expr = sys.stdin.read().strip()

        if not expr:
            print("Error: Expression required.", file=sys.stderr)
            return False

        try:
            result = manager.evaluate(expr)
            print(result)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif args.action == "stats":
        numbers = []
        if args.numbers:
            for n in args.numbers:
                try:
                    numbers.append(float(n))
                except ValueError:
                    print(f"Warning: Skipping invalid number '{n}'", file=sys.stderr)

        # Also try reading from stdin if pipeline
        if not sys.stdin.isatty():
            try:
                content = sys.stdin.read().strip()
                if content:
                    # Split by whitespace or commas
                    import re
                    parts = re.split(r'[\s,]+', content)
                    for p in parts:
                        if p:
                            try:
                                numbers.append(float(p))
                            except ValueError:
                                pass
            except (IOError, OSError):
                pass

        if not numbers:
            print("Error: No valid numbers provided.", file=sys.stderr)
            return False

        stats = manager.calculate_stats(numbers)
        print("--- Statistics ---")
        for k, v in stats.items():
            if v is None:
                print(f"{k.capitalize()}: N/A")
            elif isinstance(v, int):
                print(f"{k.capitalize()}: {v}")
            else:
                print(f"{k.capitalize()}: {v:.4f}")

    elif args.action == "prime":
        try:
            n = int(args.number)
        except ValueError:
            print("Error: Integer required.", file=sys.stderr)
            return False

        if args.subaction == "check":
            if manager.is_prime(n):
                print(f"✅ {n} is prime.")
            else:
                print(f"❌ {n} is NOT prime.")
                factors = manager.prime_factors(n)
                if len(factors) > 1:
                    print(f"Factors: {factors}")

        elif args.subaction == "next":
            print(manager.next_prime(n))

        elif args.subaction == "factors":
            factors = manager.prime_factors(n)
            print(f"Prime factors of {n}: {factors}")

    return True
