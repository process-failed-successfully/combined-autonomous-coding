import sys
import json
from typing import List, Any
from jsonpath_ng.ext import parse


class JsonPathLabManager:
    """
    Manages JSONPath evaluation on JSON data.
    """

    def evaluate(self, data: Any, path: str) -> List[Any]:
        """
        Evaluates a JSONPath expression against JSON data.
        Returns a list of matched values.
        """
        if not path:
            return [data]
        try:
            jsonpath_expr = parse(path)
            matches = jsonpath_expr.find(data)
            return [match.value for match in matches]
        except Exception as e:
            raise ValueError(f"Invalid JSONPath expression: {e}")


def run_jsonpath_lab_logic(args):
    """CLI Entry point for JSONPath Lab."""
    manager = JsonPathLabManager()

    content = ""
    if args.input:
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
        print(f"Error evaluating JSONPath: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No matches found.")
    else:
        if len(results) == 1:
            print(json.dumps(results[0], indent=2))
        else:
            print(json.dumps(results, indent=2))
    sys.exit(0)
