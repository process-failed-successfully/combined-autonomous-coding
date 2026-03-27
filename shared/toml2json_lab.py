import json
import tomlkit
import sys
from pathlib import Path


class Toml2JsonManager:
    """Manages conversion between TOML and JSON formats."""

    def convert_toml_to_json(self, input_data: str) -> str:
        """Converts TOML string to JSON string."""
        try:
            # Check if input is a file path
            if len(input_data) < 1000:
                path = Path(input_data)
                if path.exists() and path.is_file():
                    with open(path, 'r', encoding='utf-8') as f:
                        data = tomlkit.load(f)
                else:
                    data = tomlkit.parse(input_data)
            else:
                data = tomlkit.parse(input_data)

            # tomlkit.unwrap() converts TOML types back to standard python types
            # allowing json.dumps to serialize them properly
            unwrapped_data = data.unwrap()
            return json.dumps(unwrapped_data, indent=2, default=str)
        except tomlkit.exceptions.ParseError as e:
            raise ValueError(f"Invalid TOML: {e}")
        except OSError:
            # OSError can happen if file path is too long or other IO issues
            try:
                data = tomlkit.parse(input_data)
                unwrapped_data = data.unwrap()
                return json.dumps(unwrapped_data, indent=2, default=str)
            except tomlkit.exceptions.ParseError as e:
                raise ValueError(f"Invalid TOML: {e}")
        except Exception as e:
            raise ValueError(f"Error converting TOML to JSON: {e}")

    def convert_json_to_toml(self, input_data: str) -> str:
        """Converts JSON string to TOML string."""
        try:
            # Check if input is a file path
            if len(input_data) < 1000:
                path = Path(input_data)
                if path.exists() and path.is_file():
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = json.loads(input_data)
            else:
                data = json.loads(input_data)

            if not isinstance(data, dict):
                raise ValueError("JSON input must be an object (dict) to convert to TOML.")

            return tomlkit.dumps(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except OSError:
            try:
                data = json.loads(input_data)
                if not isinstance(data, dict):
                    raise ValueError("JSON input must be an object (dict) to convert to TOML.")
                return tomlkit.dumps(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error converting JSON to TOML: {e}")


def run_toml2json_lab_logic(args):
    """CLI handler for Toml2Json Lab."""
    manager = Toml2JsonManager()

    if getattr(args, "action", None) == "toml2json":
        try:
            result = manager.convert_toml_to_json(args.input)
            if getattr(args, "output", None):
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"Output written to {args.output}")
            else:
                print(result)
            return True
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "json2toml":
        try:
            result = manager.convert_json_to_toml(args.input)
            if getattr(args, "output", None):
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"Output written to {args.output}")
            else:
                print(result)
            return True
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    return False
