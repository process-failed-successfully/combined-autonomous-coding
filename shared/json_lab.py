import json
import sys
from typing import Any, List, Union
from pathlib import Path
import difflib


class JsonLabManager:
    """
    Manages JSON manipulation: query, set, delete, minify, diff.
    """

    def __init__(self):
        pass

    def load_json(self, input_data: str) -> Any:
        """Loads JSON from a string or file path."""
        try:
            # Check if input is a file path
            path = Path(input_data)
            if path.exists() and path.is_file():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            # Otherwise treat as raw JSON string
            return json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error loading JSON: {e}")

    def _parse_path(self, path: str) -> List[Union[str, int]]:
        """Parses a path string into keys and indices."""
        normalized = path.replace('[', '.').replace(']', '')
        parts = []
        for p in normalized.split('.'):
            if not p:
                continue
            if p.isdigit():
                parts.append(int(p))
            else:
                parts.append(p)
        return parts

    def get(self, data: Any, path: Union[str, List[Union[str, int]]]) -> Any:
        """Retrieves a value at the specified path."""
        if not path:
            return data

        keys = self._parse_path(path) if isinstance(path, str) else path
        current = data

        for key in keys:
            if isinstance(current, dict):
                if str(key) in current:
                    current = current[str(key)]
                elif isinstance(key, int) and key in current:
                    # integer key in dict
                    current = current[key]
                else:
                    return None
            elif isinstance(current, list):
                if isinstance(key, int) and 0 <= key < len(current):
                    current = current[key]
                else:
                    return None
            else:
                return None

        return current

    def set(self, data: Any, path: Union[str, List[Union[str, int]]], value: Any) -> Any:
        """Sets a value at the specified path (in-place modification)."""
        if not path:
            return value  # Replaces root

        keys = self._parse_path(path) if isinstance(path, str) else path
        current = data

        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if str(key) not in current:
                    # Look ahead to see if next key is int -> create list, else dict
                    next_key = keys[i + 1]
                    if isinstance(next_key, int):
                        current[str(key)] = []
                    else:
                        current[str(key)] = {}
                current = current[str(key)]
            elif isinstance(current, list):
                if isinstance(key, int):
                    # Check if we need to extend
                    if key == len(current):
                        # We need to append a new container.
                        # Check next key to decide type
                        if i + 1 < len(keys):
                            next_key = keys[i + 1]
                            if isinstance(next_key, int):
                                current.append([])
                            else:
                                current.append({})
                        current = current[key]
                    elif 0 <= key < len(current):
                        current = current[key]
                    else:
                        raise IndexError(f"List index {key} out of range")
                else:
                    raise TypeError(f"Cannot access list with string key '{key}'")
            else:
                raise TypeError(f"Cannot traverse into non-container type at '{key}'")

        last_key = keys[-1]
        if isinstance(current, dict):
            current[str(last_key)] = value
        elif isinstance(current, list):
            if isinstance(last_key, int):
                if 0 <= last_key < len(current):
                    current[last_key] = value
                elif last_key == len(current):
                    current.append(value)
                else:
                    raise IndexError(f"List index {last_key} out of range")
            else:
                raise TypeError(f"Cannot access list with string key '{last_key}'")
        else:
            raise TypeError("Cannot set property on non-container type")

        return data

    def delete(self, data: Any, path: Union[str, List[Union[str, int]]]) -> Any:
        """Deletes a key or index at the specified path."""
        if not path:
            return None  # Delete root?

        keys = self._parse_path(path) if isinstance(path, str) else path
        current = data

        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if str(key) in current:
                    current = current[str(key)]
                else:
                    return data  # Key not found, nothing to delete
            elif isinstance(current, list):
                if isinstance(key, int) and 0 <= key < len(current):
                    current = current[key]
                else:
                    return data
            else:
                return data

        last_key = keys[-1]
        if isinstance(current, dict):
            if str(last_key) in current:
                del current[str(last_key)]
        elif isinstance(current, list):
            if isinstance(last_key, int) and 0 <= last_key < len(current):
                del current[last_key]

        return data

    def minify(self, data: Any) -> str:
        """Returns minified JSON string."""
        return json.dumps(data, separators=(',', ':'))

    def diff(self, data1: Any, data2: Any) -> str:
        """Returns a semantic diff of two JSON objects."""
        # Dump with sorted keys to ensure semantic comparison
        str1 = json.dumps(data1, indent=2, sort_keys=True)
        str2 = json.dumps(data2, indent=2, sort_keys=True)

        diff = difflib.unified_diff(
            str1.splitlines(),
            str2.splitlines(),
            fromfile="original",
            tofile="modified",
            lineterm=""
        )
        return "\n".join(diff)

    def query(self, data: Any, expression: str) -> Any:
        """
        Evaluates a Python expression on the data.
        Supported names: data, len, sorted, max, min, sum, list, dict, set, tuple, enumerate, zip, map, filter, any, all.
        """
        # Restricted evaluation environment
        allowed_names = {
            "data": data,
            "len": len,
            "sorted": sorted,
            "max": max,
            "min": min,
            "sum": sum,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "any": any,
            "all": all,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
        }

        # We explicitly disable __builtins__ to prevent access to globals/imports
        return eval(expression, {"__builtins__": {}}, allowed_names)  # nosec B307


def run_json_lab_logic(args):
    """CLI Entry point for Json Lab."""
    manager = JsonLabManager()

    if args.action == "get":
        try:
            data = manager.load_json(args.input)
            result = manager.get(data, args.path)
            if result is not None:
                if isinstance(result, (dict, list)):
                    print(json.dumps(result, indent=2))
                else:
                    print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "set":
        try:
            data = manager.load_json(args.input)

            # Parse value (try JSON, then int/float, then string)
            val = args.value
            try:
                val = json.loads(args.value)
            except Exception:
                pass  # Keep as string

            result = manager.set(data, args.path, val)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "del":
        try:
            data = manager.load_json(args.input)
            result = manager.delete(data, args.path)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "minify":
        try:
            # Read from stdin if input is "-"
            if args.input == "-":
                content = sys.stdin.read()
                data = json.loads(content)
            else:
                data = manager.load_json(args.input)
            print(manager.minify(data))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "diff":
        try:
            data1 = manager.load_json(args.file1)
            data2 = manager.load_json(args.file2)
            diff = manager.diff(data1, data2)
            if diff:
                print(diff)
                sys.exit(1)  # Exit 1 if difference found (like diff command)
            else:
                sys.exit(0)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "query":
        try:
            data = manager.load_json(args.input)
            result = manager.query(data, args.path)
            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2, default=str))
            else:
                print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
