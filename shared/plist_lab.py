import sys
import json
import plistlib
from pathlib import Path


class PlistManager:
    """Manages conversion between Apple Property List (Plist) and JSON formats."""

    def plist_to_json(self, input_data: str) -> str:
        """Converts Plist string or binary data to JSON string."""
        try:
            # Check if input is a file path
            if len(input_data) < 1000:
                path = Path(input_data)
                if path.exists() and path.is_file():
                    with open(path, 'rb') as f:
                        data = plistlib.load(f)
                else:
                    data = plistlib.loads(input_data.encode('utf-8'))
            else:
                data = plistlib.loads(input_data.encode('utf-8'))

            if data is None:
                return ""

            # Use custom encoder to handle bytes objects if they appear in plists
            class PlistEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, bytes):
                        return obj.decode('utf-8', errors='replace')
                    return super().default(obj)

            return json.dumps(data, indent=2, cls=PlistEncoder)
        except plistlib.InvalidFileException as e:
            raise ValueError(f"Invalid Plist format: {e}")
        except OSError:
            try:
                data = plistlib.loads(input_data.encode('utf-8'))
                if data is None:
                    return ""

                class PlistEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, bytes):
                            return obj.decode('utf-8', errors='replace')
                        return super().default(obj)

                return json.dumps(data, indent=2, cls=PlistEncoder)
            except plistlib.InvalidFileException as e:
                raise ValueError(f"Invalid Plist format: {e}")
        except Exception as e:
            raise ValueError(f"Error converting Plist to JSON: {e}")

    def json_to_plist(self, input_data: str, fmt=plistlib.FMT_XML) -> str:
        """Converts JSON string to Plist string (XML format by default)."""
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

            if data is None:
                return ""

            if not isinstance(data, (dict, list)):
                raise ValueError("JSON input must be an object or list to convert to Plist.")

            plist_bytes = plistlib.dumps(data, fmt=fmt)
            return plist_bytes.decode('utf-8')
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except OSError:
            try:
                data = json.loads(input_data)
                if data is None:
                    return ""
                if not isinstance(data, (dict, list)):
                    raise ValueError("JSON input must be an object or list to convert to Plist.")
                plist_bytes = plistlib.dumps(data, fmt=fmt)
                return plist_bytes.decode('utf-8')
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Error converting JSON to Plist: {e}")


def run_plist_lab_logic(args):
    """CLI handler for Plist Lab."""
    manager = PlistManager()

    if getattr(args, "action", None) == "plist2json":
        try:
            result = manager.plist_to_json(args.input)
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

    elif getattr(args, "action", None) == "json2plist":
        try:
            result = manager.json_to_plist(args.input)
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
