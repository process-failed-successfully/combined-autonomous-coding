import json
import sys
import jmespath
from typing import Any, Dict, List, Union


class JmesPathLabManager:
    """Manages JMESPath evaluation on JSON data."""

    def evaluate(self, data: Union[Dict[str, Any], List[Any]], expression: str) -> Any:
        """
        Evaluates a JMESPath expression against JSON data.

        Args:
            data: The parsed JSON data (dict or list).
            expression: The JMESPath query string.

        Returns:
            The matched results.
        """
        try:
            result = jmespath.search(expression, data)
            return result
        except jmespath.exceptions.JMESPathError as e:
            raise ValueError(f"Invalid JMESPath expression: {e}")


def run_jmespath_lab_logic(args):
    """CLI Entry point for JMESPath Lab."""
    manager = JmesPathLabManager()

    if not args.expression:
        print("Error: --expression is required.", file=sys.stderr)
        sys.exit(1)

    json_data = None
    if getattr(args, "file", None):
        try:
            with open(args.file, "r") as f:
                json_data = json.load(f)
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif getattr(args, "text", None):
        try:
            json_data = json.loads(args.text)
        except Exception as e:
            print(f"Error parsing JSON text: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin if no file or text provided
        if not sys.stdin.isatty():
            try:
                json_data = json.load(sys.stdin)
            except Exception as e:
                print(f"Error parsing JSON from stdin: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: Please provide JSON via --file, --text, or stdin.", file=sys.stderr)
            sys.exit(1)

    try:
        result = manager.evaluate(json_data, args.expression)
        if result is None:
            print("null")
        else:
            print(json.dumps(result, indent=2))
        sys.exit(0)
    except ValueError as e:
        print(f"Error evaluating JMESPath: {e}", file=sys.stderr)
        sys.exit(1)
