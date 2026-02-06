import re
import itertools
import ast
from typing import Dict, Any


class LogicLabManager:
    """Manages the Logic Lab (Truth Table Generator)."""

    def __init__(self):
        pass

    def _safe_eval(self, node, context):
        """Recursively evaluate the AST node."""
        if isinstance(node, ast.Expression):
            return self._safe_eval(node.body, context)
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(self._safe_eval(v, context) for v in node.values)
            elif isinstance(node.op, ast.Or):
                return any(self._safe_eval(v, context) for v in node.values)
        elif isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                return not self._safe_eval(node.operand, context)
        elif isinstance(node, ast.BinOp):
            # Support XOR (using ^ operator)
            if isinstance(node.op, ast.BitXor):
                return bool(self._safe_eval(node.left, context)) ^ bool(self._safe_eval(node.right, context))
        elif isinstance(node, ast.Name):
            return context.get(node.id, False)
        elif isinstance(node, ast.Constant):
             return bool(node.value)

        raise ValueError(f"Unsupported operation or unsafe construct: {type(node).__name__}")

    def generate_truth_table(self, expression: str) -> Dict[str, Any]:
        """
        Generates a truth table for a boolean expression.

        Args:
            expression: The boolean expression (e.g., "A and (B or !C)").

        Returns:
            Dict containing:
                - variables: List of variable names.
                - rows: List of dicts with 'values' (var -> bool) and 'result' (bool).
                - error: Error message if any.
        """
        if not expression.strip():
            return {"variables": [], "rows": [], "error": "Empty expression."}

        # 1. Normalize Expression
        expr = expression.lower()

        # Replace operators
        symbol_replacements = {
            "&&": " and ",
            "&": " and ",
            "||": " or ",
            "|": " or ",
            "!": " not ",
            "~": " not ",
        }
        for k, v in symbol_replacements.items():
            expr = expr.replace(k, v)

        # Word replacements
        word_replacements = {
            "xor": "^",
            "true": "True",
            "false": "False"
        }
        for k, v in word_replacements.items():
            expr = re.sub(r'\b' + re.escape(k) + r'\b', v, expr)

        expr = expr.strip()

        # 2. Extract Variables
        tokens = re.findall(r'\b[a-z_][a-z0-9_]*\b', expr)
        keywords = {"and", "or", "not", "true", "false"}
        variables = sorted(list(set(t for t in tokens if t not in keywords)))

        # 3. Generate Truth Table
        rows = []
        try:
            # Parse the expression into AST
            tree = ast.parse(expr, mode='eval')

            # Generate all 2^N combinations
            for values in itertools.product([False, True], repeat=len(variables)):
                ctx = dict(zip(variables, values))

                # Use safe evaluation instead of eval()
                result = self._safe_eval(tree, ctx)

                rows.append({
                    "values": ctx,
                    "result": bool(result)
                })

            return {"variables": variables, "rows": rows, "error": None}

        except SyntaxError:
            return {"variables": [], "rows": [], "error": "Syntax Error in expression."}
        except ValueError as e:
             return {"variables": [], "rows": [], "error": str(e)}
        except Exception as e:
            return {"variables": [], "rows": [], "error": f"Evaluation error: {e}"}
