import json
import sys
from typing import Any, List, Union, Dict
from pathlib import Path
import tomlkit
from tomlkit.toml_document import TOMLDocument

class TomlLabManager:
    """
    Manages TOML manipulation: query, set, delete, format, merge, validate.
    Uses tomlkit to preserve comments and structure.
    """

    def load_toml(self, input_data: str) -> TOMLDocument:
        """Loads TOML from a string or file path."""
        try:
            # Check if input is a file path
            path = Path(input_data)
            if path.exists() and path.is_file():
                with open(path, 'r', encoding='utf-8') as f:
                    return tomlkit.load(f)
            # Otherwise treat as raw TOML string
            return tomlkit.parse(input_data)
        except Exception as e:
            # If input_data is a string that looks like a path but isn't
            if isinstance(input_data, str) and '\n' not in input_data and not input_data.strip().startswith('['):
                 pass

            try:
                return tomlkit.parse(input_data)
            except Exception:
                raise ValueError(f"Error loading TOML: {e}")

    def dump_toml(self, data: Any) -> str:
        """Dumps data to a TOML string."""
        return tomlkit.dumps(data)

    def _parse_path(self, path: Union[str, List[Union[str, int]]]) -> List[Union[str, int]]:
        """Parses a path string into keys and indices (dot notation)."""
        if isinstance(path, list):
            return path
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
            if hasattr(current, "get") or isinstance(current, dict):
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

        # Unwrap tomlkit objects if needed for pure python usage,
        # but for manipulation we might want to keep them.
        # For 'get' command output, tomlkit types stringify well.
        return current

    def set(self, data: Any, path: str, value: Any) -> Any:
        """Sets a value at the specified path (in-place modification)."""
        if not path:
            return value

        keys = self._parse_path(path)
        current = data

        for i, key in enumerate(keys[:-1]):
            if hasattr(current, "get") or isinstance(current, dict):
                if str(key) not in current:
                    next_key = keys[i+1]
                    if isinstance(next_key, int):
                        # Use tomlkit array if possible, or list
                        current[str(key)] = []
                    else:
                        current[str(key)] = tomlkit.table()
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
                                 current.append(tomlkit.table())
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
        if hasattr(current, "get") or isinstance(current, dict):
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
            return None

        keys = self._parse_path(path)
        current = data

        for i, key in enumerate(keys[:-1]):
            if hasattr(current, "get") or isinstance(current, dict):
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
        if hasattr(current, "get") or isinstance(current, dict):
            if str(last_key) in current:
                del current[str(last_key)]
        elif isinstance(current, list):
            if isinstance(last_key, int) and 0 <= last_key < len(current):
                del current[last_key]

        return data

    def merge(self, base: Any, override: Any) -> Any:
        """Recursively merges override into base."""
        if (hasattr(base, "get") or isinstance(base, dict)) and (hasattr(override, "get") or isinstance(override, dict)):
            for k, v in override.items():
                if k in base:
                    base[k] = self.merge(base[k], v)
                else:
                    base[k] = v
            return base
        return override

    def to_json(self, data: Any) -> str:
        """Converts data to JSON string."""
        # tomlkit objects are not directly serializable by json, need to unwrap
        return json.dumps(data.unwrap(), indent=2)

    def validate(self, input_data: str) -> bool:
        """Validates if input is valid TOML."""
        try:
            self.load_toml(input_data)
            return True
        except ValueError:
            return False

def run_toml_lab_logic(args):
    """CLI Entry point for Toml Lab."""
    manager = TomlLabManager()

    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching TOML Lab TUI...")
        app = AgentTUI(project_dir=Path("."), start_tab="tab-toml")
        app.run()
        sys.exit(0)

    def load_input():
        if not hasattr(args, 'input') or not args.input:
             # Try reading from stdin if available?
             # For now, require --input or argument
             print("Error: Input required.", file=sys.stderr)
             sys.exit(1)

        # If input is "-", read from stdin
        if args.input == "-":
            return manager.load_toml(sys.stdin.read())
        return manager.load_toml(args.input)

    if args.action == "get":
        try:
            data = load_input()
            result = manager.get(data, args.path)
            if result is not None:
                if hasattr(result, "unwrap"):
                     # If it's a container, dump it as TOML or JSON?
                     # Standard behavior in yaml-lab is dumping as YAML.
                     print(manager.dump_toml(result))
                elif isinstance(result, (dict, list)):
                     print(manager.dump_toml(result))
                else:
                    print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "set":
        try:
            data = load_input()
            # Try to parse value as JSON/TOML value, else string
            val = args.value
            try:
                val = json.loads(args.value)
            except:
                pass # Keep as string

            result = manager.set(data, args.path, val)
            print(manager.dump_toml(result))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "del":
        try:
            data = load_input()
            result = manager.delete(data, args.path)
            print(manager.dump_toml(result))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "format":
        try:
            data = load_input()
            print(manager.dump_toml(data))
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

    elif args.action == "to-toml":
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
             print(manager.dump_toml(data))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "merge":
        try:
            base = manager.load_toml(args.base)
            override = manager.load_toml(args.override)
            result = manager.merge(base, override)
            print(manager.dump_toml(result))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        try:
            content = args.input
            if content == "-":
                content = sys.stdin.read()

            path = Path(content)
            if path.exists() and path.is_file():
                content = path.read_text(encoding='utf-8')

            if manager.validate(content):
                print("✅ Valid TOML.")
                sys.exit(0)
            else:
                print("❌ Invalid TOML.")
                sys.exit(1)
        except Exception as e:
             if args.input == "-":
                 valid = manager.validate(sys.stdin.read())
             else:
                 valid = manager.validate(args.input)

             if valid:
                print("✅ Valid TOML.")
                sys.exit(0)
             else:
                print("❌ Invalid TOML.")
                sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
