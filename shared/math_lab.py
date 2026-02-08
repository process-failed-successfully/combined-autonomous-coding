import ast
import math
import statistics
from typing import List, Union, Dict, Any

class MathLabManager:
    """Manages the Math Lab (Math Utilities)."""

    ALLOWED_NAMES = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    ALLOWED_NAMES.update({
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
    })

    def _safe_eval(self, node):
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant):
            val = node.value
            if isinstance(val, (int, float)):
                return val
            raise ValueError(f"Unsupported constant type: {type(val)}")
        elif isinstance(node, ast.UnaryOp):
            op = node.op
            operand = self._safe_eval(node.operand)
            if isinstance(op, ast.UAdd):
                return +operand
            elif isinstance(op, ast.USub):
                return -operand
            raise ValueError(f"Unsupported unary operator: {type(op).__name__}")
        elif isinstance(node, ast.BinOp):
            op = node.op
            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            if isinstance(op, ast.Add):
                return left + right
            elif isinstance(op, ast.Sub):
                return left - right
            elif isinstance(op, ast.Mult):
                return left * right
            elif isinstance(op, ast.Div):
                return left / right
            elif isinstance(op, ast.FloorDiv):
                return left // right
            elif isinstance(op, ast.Mod):
                return left % right
            elif isinstance(op, ast.Pow):
                return left ** right
            elif isinstance(op, ast.BitXor): # Interpret ^ as exponentiation for convenience
                return left ** right
            raise ValueError(f"Unsupported binary operator: {type(op).__name__}")
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name not in self.ALLOWED_NAMES:
                raise ValueError(f"Unsupported function: {func_name}")
            args = [self._safe_eval(arg) for arg in node.args]
            return self.ALLOWED_NAMES[func_name](*args)
        elif isinstance(node, ast.Name):
            if node.id in self.ALLOWED_NAMES:
                 return self.ALLOWED_NAMES[node.id]
            # Allow constants like pi, e
            if node.id == "pi": return math.pi
            if node.id == "e": return math.e
            if node.id == "tau": return math.tau
            if node.id == "inf": return math.inf
            if node.id == "nan": return math.nan
            raise ValueError(f"Unsupported name: {node.id}")

        raise ValueError(f"Unsupported AST node: {type(node).__name__}")

    def evaluate_expression(self, expression: str) -> Union[int, float]:
        """Evaluates a mathematical expression safely."""
        try:
            tree = ast.parse(expression, mode='eval')
            return self._safe_eval(tree)
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}")

    def calculate_stats(self, data: List[float]) -> Dict[str, float]:
        """Calculates basic statistics for a list of numbers."""
        if not data:
            return {}

        stats = {
            "count": len(data),
            "min": min(data),
            "max": max(data),
            "sum": sum(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
        }

        try:
            stats["mode"] = statistics.mode(data)
        except statistics.StatisticsError:
            stats["mode"] = None # No unique mode

        if len(data) > 1:
            stats["stdev"] = statistics.stdev(data)
            stats["variance"] = statistics.variance(data)

        return stats

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

    def generate_primes(self, start: int, end: int) -> List[int]:
        """Generates a list of prime numbers in a range."""
        return [n for n in range(start, end + 1) if self.is_prime(n)]

def run_math_lab_logic(args):
    manager = MathLabManager()

    if args.action == "eval":
        try:
            result = manager.evaluate_expression(args.expression)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            return False

    elif args.action == "stats":
        data = []
        if args.data:
            try:
                data = [float(x) for x in args.data.split(",")]
            except ValueError:
                print("Error: Invalid data format. Use comma-separated numbers.")
                return False
        else:
            print("Error: --data is required for stats.")
            return False

        stats = manager.calculate_stats(data)
        print("--- Statistics ---")
        for k, v in stats.items():
            print(f"{k.capitalize()}: {v}")

    elif args.action == "prime":
        if args.check:
            try:
                n = int(args.check)
                if manager.is_prime(n):
                    print(f"{n} is prime.")
                else:
                    print(f"{n} is NOT prime.")
            except ValueError:
                print("Error: Invalid number for --check.")
                return False
        elif args.range:
            try:
                start, end = map(int, args.range.split("-"))
                primes = manager.generate_primes(start, end)
                print(f"Primes between {start} and {end}: {primes}")
            except ValueError:
                print("Error: Invalid range format. Use start-end (e.g. 1-100).")
                return False
        else:
            print("Error: --check or --range is required for prime.")
            return False

    return True
