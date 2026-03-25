import json
import yaml  # type: ignore
import sys
from pathlib import Path


class Yaml2JsonManager:
    """Manages conversion between YAML and JSON formats."""

    def convert_yaml_to_json(self, input_data: str) -> str:
        """Converts YAML string to JSON string."""
        try:
            # Check if input is a file path
            if len(input_data) < 1000:
                path = Path(input_data)
                if path.exists() and path.is_file():
                    with open(path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                else:
                    data = yaml.safe_load(input_data)
            else:
                data = yaml.safe_load(input_data)

            if data is None:
                return "{}"
            return json.dumps(data, indent=2)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        except OSError:
            # OSError can happen if file path is too long or other IO issues
            try:
                data = yaml.safe_load(input_data)
                if data is None:
                    return "{}"
                return json.dumps(data, indent=2)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML: {e}")
        except Exception as e:
            raise ValueError(f"Error converting YAML to JSON: {e}")

    def convert_json_to_yaml(self, input_data: str) -> str:
        """Converts JSON string to YAML string."""
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

            return yaml.dump(data, sort_keys=False, default_flow_style=False)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except OSError:
            try:
                data = json.loads(input_data)
                return yaml.dump(data, sort_keys=False, default_flow_style=False)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error converting JSON to YAML: {e}")


def run_yaml2json_lab_logic(args):
    """CLI handler for Yaml2Json Lab."""
    manager = Yaml2JsonManager()

    if getattr(args, "action", None) == "yaml2json":
        try:
            result = manager.convert_yaml_to_json(args.input)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"Output written to {args.output}")
            else:
                print(result)
            return True
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    elif getattr(args, "action", None) == "json2yaml":
        try:
            result = manager.convert_json_to_yaml(args.input)
            if args.output:
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
