import yaml
import tomlkit
import sys
from pathlib import Path


class Yaml2TomlManager:
    """Manages conversion between YAML and TOML formats."""

    def convert_yaml_to_toml(self, input_data: str) -> str:
        """Converts YAML string to TOML string."""
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

            if not isinstance(data, dict):
                raise ValueError("YAML input must be an object (dict) to convert to TOML.")

            return tomlkit.dumps(data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        except OSError:
            # OSError can happen if file path is too long or other IO issues
            try:
                data = yaml.safe_load(input_data)
                if not isinstance(data, dict):
                    raise ValueError("YAML input must be an object (dict) to convert to TOML.")
                return tomlkit.dumps(data)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML: {e}")
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise ValueError(f"Error converting YAML to TOML: {e}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Error converting YAML to TOML: {e}")

    def convert_toml_to_yaml(self, input_data: str) -> str:
        """Converts TOML string to YAML string."""
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
            unwrapped_data = data.unwrap()
            return yaml.dump(unwrapped_data, sort_keys=False, default_flow_style=False)
        except tomlkit.exceptions.ParseError as e:
            raise ValueError(f"Invalid TOML: {e}")
        except OSError:
            try:
                data = tomlkit.parse(input_data)
                unwrapped_data = data.unwrap()
                return yaml.dump(unwrapped_data, sort_keys=False, default_flow_style=False)
            except tomlkit.exceptions.ParseError as e:
                raise ValueError(f"Invalid TOML: {e}")
            except Exception as e:
                raise ValueError(f"Error converting TOML to YAML: {e}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Error converting TOML to YAML: {e}")


def run_yaml2toml_lab_logic(args):
    """CLI handler for Yaml2Toml Lab."""
    manager = Yaml2TomlManager()

    if getattr(args, "action", None) == "yaml2toml":
        try:
            result = manager.convert_yaml_to_toml(args.input)
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

    elif getattr(args, "action", None) == "toml2yaml":
        try:
            result = manager.convert_toml_to_yaml(args.input)
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
