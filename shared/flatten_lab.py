import json
import sys
from typing import Any, Dict, List, Union

class FlattenManager:
    """Manages JSON flattening and unflattening operations."""

    def __init__(self, separator: str = "."):
        self.separator = separator

    def flatten(self, data: Union[Dict[str, Any], List[Any]], parent_key: str = '') -> Dict[str, Any]:
        """Flattens a nested dictionary or list."""
        items: List[tuple] = []
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{self.separator}{k}" if parent_key else k
                if isinstance(v, (dict, list)) and v:  # don't recurse on empty dict/list
                    items.extend(self.flatten(v, new_key).items())
                else:
                    items.append((new_key, v))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                new_key = f"{parent_key}{self.separator}{i}" if parent_key else str(i)
                if isinstance(v, (dict, list)) and v:
                    items.extend(self.flatten(v, new_key).items())
                else:
                    items.append((new_key, v))
        else:
            if parent_key:
                items.append((parent_key, data))
            else:
                return data

        return dict(items)

    def unflatten(self, flat_data: Dict[str, Any]) -> Union[Dict[str, Any], List[Any]]:
        """Unflattens a flat dictionary with separated keys into a nested structure."""
        if not isinstance(flat_data, dict):
            return flat_data

        unflattened: Dict[str, Any] = {}

        for key, value in flat_data.items():
            parts = key.split(self.separator)
            current = unflattened
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    current[part] = value
                else:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

        return self._convert_numeric_keys_to_lists(unflattened)

    def _convert_numeric_keys_to_lists(self, data: Any) -> Any:
        """Recursively converts dicts with purely sequential numeric keys starting at 0 into lists."""
        if isinstance(data, dict):
            # Check if all keys are sequential integers starting from 0
            if data and all(k.isdigit() for k in data.keys()):
                keys = [int(k) for k in data.keys()]
                if sorted(keys) == list(range(len(keys))):
                    return [self._convert_numeric_keys_to_lists(data[str(i)]) for i in range(len(keys))]

            # If not a purely sequential numeric dictionary, just recurse
            return {k: self._convert_numeric_keys_to_lists(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_numeric_keys_to_lists(item) for item in data]
        else:
            return data


def run_flatten_lab_logic(args) -> bool:
    """CLI logic for the Flatten Lab."""
    manager = FlattenManager(separator=args.separator)

    input_text = None
    if args.text:
        input_text = args.text
    elif args.file:
        try:
            with open(args.file, "r") as f:
                input_text = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}", file=sys.stderr)
            return False
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()

    if not input_text:
        print("❌ Error: No input data provided. Use --text, --file, or stdin.", file=sys.stderr)
        return False

    try:
        data = json.loads(input_text)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}", file=sys.stderr)
        return False

    if args.action == "flatten":
        result = manager.flatten(data)
    elif args.action == "unflatten":
        if not isinstance(data, dict):
            print("❌ Error: Input to unflatten must be a JSON object (dictionary).", file=sys.stderr)
            return False
        result = manager.unflatten(data)
    else:
        print(f"❌ Error: Unknown action '{args.action}'.", file=sys.stderr)
        return False

    try:
        output_str = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_str)
            print(f"✅ Saved to {args.output}")
        else:
            print(output_str)
        return True
    except Exception as e:
        print(f"❌ Error formatting or writing output: {e}", file=sys.stderr)
        return False
