import sys
import json
from pathlib import Path
from typing import Any, List, Union, Dict

try:
    import yaml
except ImportError:
    yaml = None

class YamlLabManager:
    """
    Manages YAML manipulation: query, set, delete, merge, validate.
    """

    def __init__(self):
        if yaml is None:
            raise ImportError("PyYAML is not installed. Please install it with `pip install PyYAML`.")

    def load_yaml(self, input_data: str) -> Any:
        """Loads YAML from a string or file path."""
        try:
            # Check if input is a file path
            is_file = False
            try:
                path = Path(input_data)
                # Check length to avoid OSError on some systems, and handle OSError from exists()
                if len(str(input_data)) < 4096:  # Reasonable limit for a path
                    if path.exists() and path.is_file():
                        is_file = True
            except OSError:
                # If path is too long or invalid OS path, it's likely raw YAML content
                pass

            if is_file:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            # Otherwise treat as raw YAML string
            return yaml.safe_load(input_data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        except Exception as e:
            raise ValueError(f"Error loading YAML: {e}")

    def _parse_path(self, path: str) -> List[Union[str, int]]:
        """Parses a path string into keys and indices."""
        normalized = path.replace('[', '.').replace(']', '')
        parts = []
        for p in normalized.split('.'):
            if not p: continue
            if p.isdigit():
                parts.append(int(p))
            else:
                parts.append(p)
        return parts

    def get(self, data: Any, path: str) -> Any:
        """Retrieves a value at the specified path."""
        if not path:
            return data

        keys = self._parse_path(path)
        current = data

        for key in keys:
            if isinstance(current, dict):
                if str(key) in current:
                    current = current[str(key)]
                elif isinstance(key, int) and key in current: # integer key in dict
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

    def set(self, data: Any, path: str, value: Any) -> Any:
        """Sets a value at the specified path (in-place modification)."""
        if not path:
            return value # Replaces root

        keys = self._parse_path(path)
        current = data

        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if str(key) not in current:
                    # Look ahead to see if next key is int -> create list, else dict
                    next_key = keys[i+1]
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

    def delete(self, data: Any, path: str) -> Any:
        """Deletes a key or index at the specified path."""
        if not path:
            return None # Delete root?

        keys = self._parse_path(path)
        current = data

        for i, key in enumerate(keys[:-1]):
            if isinstance(current, dict):
                if str(key) in current:
                    current = current[str(key)]
                else:
                    return data # Key not found, nothing to delete
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

    def merge(self, data1: Any, data2: Any) -> Any:
        """Deep merges data2 into data1."""
        if isinstance(data1, dict) and isinstance(data2, dict):
            for k, v in data2.items():
                if k in data1:
                    data1[k] = self.merge(data1[k], v)
                else:
                    data1[k] = v
            return data1
        # For lists, we could append or replace. Standard override usually replaces for scalar/list.
        # But if both are lists, appending might be desired?
        # For simplicity and consistency with standard "override" behavior:
        return data2

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
    try:
        manager = YamlLabManager()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.action == "get":
        try:
            data = manager.load_yaml(args.input)
            result = manager.get(data, args.path)
            if result is not None:
                print(yaml.safe_dump(result, default_flow_style=False).strip())
            else:
                # Optionally print nothing or null
                pass
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "set":
        try:
            data = manager.load_yaml(args.input)

            # Parse value (try JSON/YAML parsing for complex values, else string)
            val = args.value
            try:
                # yaml.safe_load can parse "true", "123", "[1,2]" etc correctly
                val = yaml.safe_load(args.value)
            except:
                pass

            result = manager.set(data, args.path, val)
            print(yaml.safe_dump(result, default_flow_style=False).strip())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "del":
        try:
            data = manager.load_yaml(args.input)
            result = manager.delete(data, args.path)
            print(yaml.safe_dump(result, default_flow_style=False).strip())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "merge":
        try:
            data1 = manager.load_yaml(args.file1)
            data2 = manager.load_yaml(args.file2)
            result = manager.merge(data1, data2)
            print(yaml.safe_dump(result, default_flow_style=False).strip())
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "to-json":
        try:
            data = manager.load_yaml(args.input)
            print(manager.to_json(data))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        try:
            if args.input == "-":
                content = sys.stdin.read()
            else:
                # Check if file
                path = Path(args.input)
                if path.exists():
                    content = path.read_text()
                else:
                    content = args.input # Treat as string

            if manager.validate(content):
                print("✅ Valid YAML.")
                sys.exit(0)
            else:
                print("❌ Invalid YAML.")
                sys.exit(1)
        except Exception as e:
             print(f"Error: {e}", file=sys.stderr)
             sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
