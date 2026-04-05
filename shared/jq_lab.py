import sys
import json
from typing import Any
try:
    import jq
except ImportError:
    jq = None


class JqLabManager:
    """
    Manages jq evaluation on JSON data.
    """

    def evaluate(self, data: Any, filter_expr: str) -> Any:
        """
        Evaluates a jq filter expression against JSON data.
        Returns the matched values.
        """
        if not filter_expr:
            return data
        try:
            compiled = jq.compile(filter_expr)
            result = compiled.input_value(data).all()
            if len(result) == 0:
                return None
            if len(result) == 1:
                return result[0]
            return result
        except Exception as e:
            raise ValueError(f"Invalid jq expression: {e}")


def run_jq_lab_logic(args):
    """CLI Entry point for jq Lab."""
    manager = JqLabManager()

    content = ""
    if getattr(args, 'input', None):
        if args.input == "-":
            content = sys.stdin.read()
        else:
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                sys.exit(1)
    else:
        print("Error: Input file or stdin required.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        results = manager.evaluate(data, args.expression)
    except ValueError as e:
        print(f"Error evaluating jq: {e}", file=sys.stderr)
        sys.exit(1)

    if results is None:
        print("No matches found.")
    else:
        print(json.dumps(results, indent=2))
    sys.exit(0)
