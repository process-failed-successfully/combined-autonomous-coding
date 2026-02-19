import yaml
import json
import sys
from typing import Any, List, Optional, Union, Dict
from pathlib import Path

class YamlLabManager:
    """
    Manages YAML manipulation: query, set, delete, format, merge, validate.
    """

    def load_yaml(self, input_data: str) -> Any:
        """Loads YAML from a string or file path."""
        try:
            # Check if input is a file path
            path = Path(input_data)
            if path.exists() and path.is_file():
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            # Otherwise treat as raw YAML string
            return yaml.safe_load(input_data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        except Exception as e:
            # In case input_data is a string that looks like a path but isn't
            # or if it's just raw yaml that happens to match a path structure (unlikely)
            # Fallback to loading as string if file load failed?
            # Actually, if path exists but fails to read, it's an error.
            # If path doesn't exist, we try to load as string.
            if isinstance(input_data, str) and '\n' not in input_data and not input_data.strip().startswith(('{', '[', '-', '%', '!')):
                 # It might have been intended as a file path
                 pass

            try:
                return yaml.safe_load(input_data)
            except Exception:
                raise ValueError(f"Error loading YAML: {e}")

    def dump_yaml(self, data: Any) -> str:
        """Dumps data to a YAML string."""
        return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)

    def _parse_path(self, path: Union[str, List[Union[str, int]]]) -> List[Union[str, int]]:
        """Parses a path string into keys and indices (dot notation), or returns list as is."""
        if isinstance(path, list):
            return path

        # Reusing logic similar to JsonLabManager
        normalized = path.replace('[', '.').replace(']', '')
        parts: List[Union[str, int]] = []
        for p in normalized.split('.'):
            if not p: continue
            if p.isdigit():
                parts.append(int(p))
            else:
                parts.append(p)
        return parts

    def get(self, data: Any, path: Union[str, List[Union[str, int]]]) -> Any:
        """Retrieves a value at the specified path."""
        if not path:
            return data

        keys = self._parse_path(path)
        current = data

        for key in keys:
            if isinstance(current, dict):
                if str(key) in current:
                    current = current[str(key)]
                elif isinstance(key, int) and key in current:
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
            return value

        keys = self._parse_path(path)
        current = data

        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if str(key) not in current:
                    next_key = keys[i+1]
                    if isinstance(next_key, int):
                        current[str(key)] = []
                    else:
                        current[str(key)] = {}
                current = current[str(key)]
            elif isinstance(current, list):
                if isinstance(key, int):
                    if key == len(current):
                        # Append new container
                        if i + 1 < len(keys):
                             next_key = keys[i+1]
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
             raise TypeError(f"Cannot set property on non-container type")

        return data

    def delete(self, data: Any, path: Union[str, List[Union[str, int]]]) -> Any:
        """Deletes a key or index at the specified path."""
        if not path:
            return None

        keys = self._parse_path(path)
        current = data

        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if str(key) in current:
                    current = current[str(key)]
                else:
                    return data
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

    def merge(self, base: Any, override: Any) -> Any:
        """Recursively merges override into base."""
        if isinstance(base, dict) and isinstance(override, dict):
            for k, v in override.items():
                if k in base:
                    base[k] = self.merge(base[k], v)
                else:
                    base[k] = v
            return base
        return override

    def to_json(self, data: Any) -> str:
        """Converts data to JSON string."""
        return json.dumps(data, indent=2)

    def validate(self, input_data: str) -> bool:
        """Validates if input is valid YAML."""
        try:
            self.load_yaml(input_data)
            return True
        except ValueError:
            return False

def run_yaml_lab_logic(args):
    """CLI Entry point for Yaml Lab."""
    manager = YamlLabManager()

    # Load input data based on action
    # Most actions require 'input' argument, except 'merge' which takes 2 files
    # and 'validate' which takes 'input'

    # Helper to load input safely
    def load_input():
        if not hasattr(args, 'input') or not args.input:
             # Try reading from stdin if available?
             # For now, require --input or argument
             print("Error: Input required.", file=sys.stderr)
             sys.exit(1)

        # If input is "-", read from stdin
        if args.input == "-":
            return manager.load_yaml(sys.stdin.read())
        return manager.load_yaml(args.input)

    if args.action == "get":
        try:
            data = load_input()
            result = manager.get(data, args.path)
            if result is not None:
                if isinstance(result, (dict, list)):
                    print(manager.dump_yaml(result))
                else:
                    print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "set":
        try:
            data = load_input()
            # Try to parse value as JSON/YAML, else string
            val = args.value
            try:
                val = json.loads(args.value)
            except:
                pass # Keep as string

            result = manager.set(data, args.path, val)
            print(manager.dump_yaml(result))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "del":
        try:
            data = load_input()
            result = manager.delete(data, args.path)
            print(manager.dump_yaml(result))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "format":
        try:
            data = load_input()
            print(manager.dump_yaml(data))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "json":
        try:
            data = load_input()
            print(manager.to_json(data))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "to-yaml":
        try:
             # Input is JSON here
             if args.input == "-":
                 content = sys.stdin.read()
             else:
                 path = Path(args.input)
                 if path.exists():
                     content = path.read_text()
                 else:
                     content = args.input

             data = json.loads(content)
             print(manager.dump_yaml(data))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "merge":
        try:
            base = manager.load_yaml(args.base)
            override = manager.load_yaml(args.override)
            result = manager.merge(base, override)
            print(manager.dump_yaml(result))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        try:
            # We don't use load_input here because we want to catch the error explicitly and print status
            # But load_input raises ValueError which is caught in Exception.
            # Let's use load_input logic manually
            content = args.input
            if content == "-":
                content = sys.stdin.read()

            # If it's a file, read it
            path = Path(content)
            if path.exists() and path.is_file():
                content = path.read_text(encoding='utf-8')

            if manager.validate(content):
                print("✅ Valid YAML.")
                sys.exit(0)
            else:
                print("❌ Invalid YAML.")
                sys.exit(1)
        except Exception as e:
             # If validation fails inside validate(), it returns False.
             # If something else happens (IOError), we print error.
             # Actually validate() handles load_yaml exceptions.
             # But here we might be passing a file path to validate() which expects content if we didn't read it?
             # manager.validate calls load_yaml which handles file paths.
             # So we can just pass args.input to validate if it's not "-"

             if args.input == "-":
                 valid = manager.validate(sys.stdin.read())
             else:
                 valid = manager.validate(args.input)

             if valid:
                print("✅ Valid YAML.")
                sys.exit(0)
             else:
                print("❌ Invalid YAML.")
                sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
