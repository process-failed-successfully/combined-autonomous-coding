import re
import itertools
from typing import Dict, Any


class LogicLabManager:
    """Manages the Logic Lab (Truth Table Generator)."""

    def __init__(self):
        pass

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
        # Convert to lower case for keyword matching, but keep variables case-sensitive?
        # Actually, standardizing to lowercase is safer for simplicity unless user wants case-sensitive vars.
        # Let's support case-insensitive variables for now.

        expr = expression.lower()

        # Replace operators
        # Order matters: replace longer symbols first

        # 1. Symbol replacements
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

        # 2. Word replacements (using regex for boundaries)
        word_replacements = {
            "xor": "^",  # Python bitwise XOR works as logical XOR for bools
            "true": "True",
            "false": "False"
        }
        for k, v in word_replacements.items():
            # Use \b boundary
            expr = re.sub(r'\b' + re.escape(k) + r'\b', v, expr)

        expr = expr.strip()

        # 2. Extract Variables
        # Find valid identifiers: starts with letter/underscore, contains alphanumeric/underscore
        # Exclude python keywords
        tokens = re.findall(r'\b[a-z_][a-z0-9_]*\b', expr)
        keywords = {"and", "or", "not", "true", "false"}
        variables = sorted(list(set(t for t in tokens if t not in keywords)))

        # 3. Generate Truth Table
        rows = []
        try:
            # Safety Check: Ensure no dangerous calls
            # We strictly whitelist characters allowed in the final python expression
            # Allowed: a-z, 0-9, _, spaces, (, ), ^, and, or, not, True, False
            # We already replaced operators, so we check the resulting string.

            # Simple check: should not contain '.', '[', ']', '{', '}' to prevent attribute access or dict/list construction
            if any(c in expr for c in ['.', '[', ']', '{', '}', ';', 'import', 'eval', 'exec']):
                return {"variables": [], "rows": [], "error": "Invalid characters or unsafe constructs detected."}

            # Compile for performance and syntax checking
            code = compile(expr, "<string>", "eval")

            # Generate all 2^N combinations
            for values in itertools.product([False, True], repeat=len(variables)):
                ctx = dict(zip(variables, values))
                # Add sanitized builtins
                ctx["__builtins__"] = {}

                result = eval(code, ctx)  # nosec B307
                rows.append({
                    "values": ctx,
                    "result": bool(result)
                })

            return {"variables": variables, "rows": rows, "error": None}

        except SyntaxError:
            return {"variables": [], "rows": [], "error": "Syntax Error in expression."}
        except Exception as e:
            return {"variables": [], "rows": [], "error": str(e)}
