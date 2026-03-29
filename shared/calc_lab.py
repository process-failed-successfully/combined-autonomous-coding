import ast
import math
import operator
import sys
from typing import Dict, Any, Union, Optional

class CalcLabManager:
    """Manages Calculator Lab operations: evaluate, bitwise, base conversion."""

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
            "bin": bin,
            "hex": hex,
            "oct": oct,
            "int": int,
            "float": float,
        })
        self.variables: Dict[str, Any] = {}

    def _safe_eval(self, node: ast.AST) -> Union[int, float, bool]:
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body)
        elif isinstance(node, ast.Constant): # Python >= 3.8
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
                if right == 0: raise ValueError("Division by zero")
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                if right == 0: raise ValueError("Division by zero")
                return left // right
            elif isinstance(node.op, ast.Mod):
                return left % right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            elif isinstance(node.op, ast.BitXor):
                return operator.xor(int(left), int(right))
            elif isinstance(node.op, ast.BitOr):
                return operator.or_(int(left), int(right))
            elif isinstance(node.op, ast.BitAnd):
                return operator.and_(int(left), int(right))
            elif isinstance(node.op, ast.LShift):
                return operator.lshift(int(left), int(right))
            elif isinstance(node.op, ast.RShift):
                return operator.rshift(int(left), int(right))
        elif isinstance(node, ast.UnaryOp):
            operand = self._safe_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
            elif isinstance(node.op, ast.Invert):
                return ~int(operand)
        elif isinstance(node, ast.Compare):
            left = self._safe_eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._safe_eval(comparator)
                if isinstance(op, ast.Eq):
                    res = left == right
                elif isinstance(op, ast.NotEq):
                    res = left != right
                elif isinstance(op, ast.Lt):
                    res = left < right
                elif isinstance(op, ast.LtE):
                    res = left <= right
                elif isinstance(op, ast.Gt):
                    res = left > right
                elif isinstance(op, ast.GtE):
                    res = left >= right
                else:
                    raise ValueError(f"Unsupported comparison operator: {type(op).__name__}")
                if not res:
                    return False
                left = right
            return True
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.allowed_names:
                    args = [self._safe_eval(arg) for arg in node.args]
                    return self.allowed_names[func_name](*args)
                else:
                    raise ValueError(f"Function '{func_name}' not allowed")
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            if node.id in self.allowed_names:
                return self.allowed_names[node.id]
            raise ValueError(f"Variable '{node.id}' not defined")
        # ast.parse(mode='eval') does not produce Assign nodes.
        # Assignments are handled at the string parsing level in evaluate().

        raise ValueError(f"Unsupported operation: {type(node).__name__}")

    def evaluate(self, expression: str) -> Union[float, int, bool]:
        """Safely evaluates a mathematical expression."""
        if not expression:
            raise ValueError("Empty expression")

        try:
            # Handle assignment manually for REPL support
            if "=" in expression and not expression.startswith("=") and "==" not in expression and "!=" not in expression and "<=" not in expression and ">=" not in expression:
                # Check if it's a valid assignment (var = expr)
                # Ensure we only split by the first '=' that isn't part of a comparison operator
                # This basic check works since we ruled out the double-character comparators above
                parts = expression.split("=", 1)
                var_name = parts[0].strip()
                expr = parts[1].strip()

                # Check if var_name is a valid identifier
                if var_name.isidentifier():
                    val = self.evaluate(expr)
                    self.variables[var_name] = val
                    return val

                # If not a valid identifier, it might be '==' check which is handled by parser if we supported it
                # But we don't support boolean checks yet in _safe_eval (Compare).
                # Fallthrough to normal eval which will likely fail or parse as something else if supported.
                # Since we don't support Compare nodes in _safe_eval, it will raise "Unsupported operation".

            tree = ast.parse(expression, mode='eval')
            return self._safe_eval(tree)
        except SyntaxError as e:
            raise ValueError(f"Invalid syntax: {e}")
        except Exception as e:
            raise ValueError(str(e))

    def format_result(self, value: Union[int, float, bool]) -> str:
        """Formats the result for display."""
        if isinstance(value, bool):
            return str(value)
        elif isinstance(value, int):
            try:
                dec_str = f"{value}"
                hex_str = f"{value:#x}"
                bin_str = f"{value:#b}"
                oct_str = f"{value:#o}"

                return (
                    f"Dec: {dec_str}\n"
                    f"Hex: {hex_str}\n"
                    f"Bin: {bin_str}\n"
                    f"Oct: {oct_str}"
                )
            except Exception:
                return str(value)
        else:
            return str(value)

    def run_repl(self):
        """Runs an interactive Read-Eval-Print Loop."""
        print("CalcLab REPL (Programmer's Calculator)")
        print("Type 'exit' or 'quit' to leave.")
        print("Supported: +, -, *, /, //, %, **, ^, &, |, ~, <<, >>")
        print("Variables: x = 10, y = x * 2")

        while True:
            try:
                expr = input("calc> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if not expr:
                continue

            if expr.lower() in ["exit", "quit"]:
                break

            if expr.lower() == "clear":
                print("\033c", end="")
                continue

            if expr.lower() == "vars":
                print(self.variables)
                continue

            try:
                result = self.evaluate(expr)
                print(self.format_result(result))
                # Store result in '_'
                self.variables['_'] = result
            except Exception as e:
                print(f"Error: {e}")

def run_calc_lab_logic(args) -> bool:
    """CLI handler for Calc Lab."""
    manager = CalcLabManager()

    # If expression provided as argument, evaluate and exit
    if args.expression:
        # Join all arguments to form the expression if list
        expr = args.expression
        if isinstance(expr, list):
            expr = " ".join(expr)

        try:
            result = manager.evaluate(expr)
            print(manager.format_result(result))
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    # Otherwise, start REPL
    manager.run_repl()
    return True
