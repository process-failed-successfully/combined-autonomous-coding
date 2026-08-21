import sys
import yaml
import json
from pathlib import Path
from typing import Any
try:
    import jq
except ImportError:
    jq = None


class YqLabManager:
    """
    Manages jq evaluation on YAML data.
    """

    def evaluate(self, data: Any, filter_expr: str) -> Any:
        """
        Evaluates a jq filter expression against YAML data (converted to dict/list).
        Returns the matched values.
        """
        if jq is None:
            raise RuntimeError("jq module is not installed")

        if not filter_expr:
            return data

        try:
            compiled = jq.compile(filter_expr)
            # data is already parsed as python objects (dict/list) from yaml
            result = compiled.input_value(data).all()
            if len(result) == 0:
                return None
            if len(result) == 1:
                return result[0]
            return result
        except Exception as e:
            raise ValueError(f"Invalid jq expression: {e}")


def run_yq_lab_logic(args):
    """CLI Entry point for yq Lab."""
    manager = YqLabManager()

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
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"Invalid YAML: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        results = manager.evaluate(data, args.expression)
    except Exception as e:
        print(f"Error evaluating yq: {e}", file=sys.stderr)
        sys.exit(1)

    if results is None:
        print("No matches found.")
    else:
        # We'll dump the result as YAML.
        # jq outputs JSON-like structures (lists/dicts/scalars), which map cleanly to YAML.
        if isinstance(results, (dict, list)):
            print(yaml.safe_dump(results, default_flow_style=False, sort_keys=False).strip())
        else:
            # Simple scalars like strings, numbers
            print(results)
    sys.exit(0)
