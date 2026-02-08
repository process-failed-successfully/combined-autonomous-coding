import ast
import math
import statistics
import sys
from typing import Union, List, Dict, Any, Optional

class MathLabManager:
    """Manages Math Lab operations: evaluation, statistics, and prime analysis."""

    def __init__(self):
        self.constants = {
            "pi": math.pi,
            "e": math.e,
            "tau": math.tau,
            "inf": float("inf"),
            "nan": float("nan"),
        }
        self.functions = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "ln": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "abs": abs,
            "floor": math.floor,
            "ceil": math.ceil,
            "round": round,
            "pow": pow,
            "min": min,
            "max": max,
        }

    def _safe_eval(self, node: ast.AST) -> Union[int, float]:
        """Recursively evaluates an AST node securely."""
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
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
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                return left // right
            elif isinstance(node.op, ast.Mod):
                return left % right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            elif isinstance(node.op, ast.BitXor):
                # Interpret ^ as exponentiation for convenience
                return left ** right
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            if isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.UAdd):
                return +operand
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self.functions:
                args = [self._safe_eval(arg) for arg in node.args]
                return self.functions[func_name](*args)
            raise ValueError(f"Unknown function: {func_name}")
        elif isinstance(node, ast.Name):
            if node.id in self.constants:
                return self.constants[node.id]
            raise ValueError(f"Unknown variable: {node.id}")
        elif isinstance(node, ast.Constant):
            return node.value

        raise ValueError(f"Unsupported syntax: {type(node).__name__}")

    def evaluate(self, expression: str) -> Union[int, float, str]:
        """Evaluates a mathematical expression string safely."""
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            return self._safe_eval(tree)
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error: {str(e)}"

    def statistics(self, numbers: List[float]) -> Dict[str, Union[float, str]]:
        """Calculates basic statistics for a list of numbers."""
        if not numbers:
            return {"error": "No numbers provided"}

        try:
            stats = {
                "count": len(numbers),
                "sum": sum(numbers),
                "min": min(numbers),
                "max": max(numbers),
                "mean": statistics.mean(numbers),
                "median": statistics.median(numbers),
                "variance": statistics.variance(numbers) if len(numbers) > 1 else 0,
                "stdev": statistics.stdev(numbers) if len(numbers) > 1 else 0,
            }
            try:
                stats["mode"] = statistics.mode(numbers)
            except statistics.StatisticsError:
                stats["mode"] = "No unique mode"

            return stats
        except Exception as e:
            return {"error": str(e)}

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

    def get_factors(self, n: int) -> List[int]:
        """Returns a list of factors of n."""
        factors = []
        for i in range(1, int(abs(n)**0.5) + 1):
            if n % i == 0:
                factors.append(i)
                if i*i != n:
                    factors.append(n // i)
        return sorted(factors)

    def next_prime(self, n: int) -> int:
        """Finds the next prime number greater than n."""
        candidate = n + 1
        while True:
            if self.is_prime(candidate):
                return candidate
            candidate += 1

    def prev_prime(self, n: int) -> Optional[int]:
        """Finds the previous prime number smaller than n."""
        candidate = n - 1
        while candidate > 1:
            if self.is_prime(candidate):
                return candidate
            candidate -= 1
        return None

    def prime_info(self, n: int) -> Dict[str, Any]:
        """Returns information about a number related to primality."""
        return {
            "number": n,
            "is_prime": self.is_prime(n),
            "factors": self.get_factors(n),
            "next_prime": self.next_prime(n),
            "prev_prime": self.prev_prime(n),
        }


def run_math_lab_logic(args) -> bool:
    """CLI handler for Math Lab."""
    manager = MathLabManager()

    if args.action == "eval":
        if not args.expression:
            print("Error: Expression is required for 'eval'.", file=sys.stderr)
            return False

        result = manager.evaluate(args.expression)
        print(result)
        return not str(result).startswith("Error")

    elif args.action == "stats":
        numbers = []
        if args.numbers:
            try:
                numbers = [float(x) for x in args.numbers]
            except ValueError:
                print("Error: Invalid number in arguments.", file=sys.stderr)
                return False
        else:
            # Read from stdin
            try:
                content = sys.stdin.read()
                numbers = [float(x) for x in content.split()]
            except ValueError:
                print("Error: Invalid number in stdin.", file=sys.stderr)
                return False

        if not numbers:
            print("Error: No numbers provided.", file=sys.stderr)
            return False

        stats = manager.statistics(numbers)
        if "error" in stats:
            print(f"Error: {stats['error']}", file=sys.stderr)
            return False

        print("--- Statistics ---")
        for k, v in stats.items():
            if isinstance(v, float):
                print(f"{k.capitalize():<10}: {v:.4f}")
            else:
                print(f"{k.capitalize():<10}: {v}")
        return True

    elif args.action == "prime":
        try:
            n = int(args.n)
        except (ValueError, TypeError):
             print("Error: Input must be an integer.", file=sys.stderr)
             return False

        info = manager.prime_info(n)
        print(f"--- Prime Info for {n} ---")
        print(f"Is Prime:   {info['is_prime']}")
        print(f"Next Prime: {info['next_prime']}")
        print(f"Prev Prime: {info['prev_prime']}")

        factors = info['factors']
        if len(factors) > 10:
            print(f"Factors:    {factors[:10]} ... ({len(factors)} total)")
        else:
            print(f"Factors:    {factors}")

        return True

    return True
