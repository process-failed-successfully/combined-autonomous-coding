import sys
import json
from typing import Any
import jmespath


class JmesPathLabManager:
    """
    Manages JMESPath evaluation on JSON data.
    """

    def evaluate(self, data: Any, path: str) -> Any:
        """
        Evaluates a JMESPath expression against JSON data.
        Returns the matched value or None if no match.
        """
        if not path:
            return data
        try:
            return jmespath.search(path, data)
        except jmespath.exceptions.JMESPathError as e:
            raise ValueError(f"Invalid JMESPath expression: {e}")


def run_jmespath_lab_logic(args):
    """CLI Entry point for JMESPath Lab."""
    manager = JmesPathLabManager()

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
    elif getattr(args, 'text', None):
        content = args.text
    else:
        print("Error: Input file, text, or stdin required.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = manager.evaluate(data, args.expression)
    except ValueError as e:
        print(f"Error evaluating JMESPath: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    sys.exit(0)
