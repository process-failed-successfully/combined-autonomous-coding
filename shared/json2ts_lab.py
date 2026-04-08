import sys
import json
import argparse
from typing import Dict, Any, List

class Json2TsManager:
    """Manager for converting JSON string to TypeScript interfaces."""

    def __init__(self):
        self.interfaces = []
        self.interface_names = set()

    def generate(self, json_str: str, root_name: str = "RootInterface") -> str:
        self.interfaces = []
        self.interface_names = set()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            # If the root is a list, try to infer from the first element
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                raise ValueError("JSON root must be an object or a list of objects.")

        self._parse_dict(data, root_name)

        return "\n\n".join(self.interfaces)

    def _parse_dict(self, data: Dict[str, Any], interface_name: str):
        # Handle duplicate interface names recursively
        original_interface_name = interface_name
        counter = 1
        while interface_name in self.interface_names:
            interface_name = f"{original_interface_name}{counter}"
            counter += 1

        self.interface_names.add(interface_name)

        fields = []
        for key, value in data.items():
            ts_type = self._infer_type(key, value)
            safe_key = self._sanitize_identifier(key)
            fields.append((safe_key, ts_type))

        interface_def = f"export interface {interface_name} {{\n"

        for name, type_str in fields:
            interface_def += f"  {name}: {type_str};\n"

        interface_def += "}"

        self.interfaces.append(interface_def)

    def _infer_type(self, key: str, value: Any) -> str:
        if value is None:
            return "any"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            if len(value) == 0:
                return "any[]"
            else:
                # Infer type from first element
                first_elem = value[0]
                if isinstance(first_elem, dict):
                    child_interface_name = self._to_pascal_case(key) + "Item"
                    self._parse_dict(first_elem, child_interface_name)
                    return f"{child_interface_name}[]"
                else:
                    item_type = self._infer_type(key, first_elem)
                    return f"{item_type}[]"
        elif isinstance(value, dict):
            child_interface_name = self._to_pascal_case(key)
            self._parse_dict(value, child_interface_name)
            return child_interface_name
        else:
            return "any"

    def _to_pascal_case(self, s: str) -> str:
        # replace non-alphanumeric with space
        s = "".join([c if c.isalnum() else " " for c in s])
        words = s.split()
        if not words:
            return "NestedInterface"
        return "".join(w.capitalize() for w in words)

    def _sanitize_identifier(self, s: str) -> str:
        if not s:
            return "field"

        # Valid javascript identifiers
        # Can start with $ or _ or letter, then digits allowed too

        # Keep original if it's already a valid identifier and not a JS reserved word
        # (Very basic check here, we'll quote it if it contains spaces or weird chars)

        is_valid_id = s.replace("_", "").replace("$", "").isalnum() and not s[0].isdigit()

        import keyword
        # Python keyword list is good enough for most JS reserved words minus a few,
        # but let's just quote if it's not a pure alphanumeric/underscore string
        # or if it starts with a number.

        if is_valid_id:
            return s
        else:
            # We wrap it in quotes if it's not a standard identifier format
            # In typescript interface we can write: "weird-key": string;
            return f'"{s}"'


def run_json2ts_lab_logic(args) -> bool:
    """CLI logic for the Json2Ts lab."""
    import sys
    manager = Json2TsManager()

    input_data = ""
    if getattr(args, 'file', None):
        try:
            with open(args.file, 'r') as f:
                input_data = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif getattr(args, 'text', None):
        input_data = args.text
    elif not sys.stdin.isatty():
        try:
            input_data = sys.stdin.read()
        except Exception:
            pass

    if not input_data:
        print("Error: No JSON input provided via --file, --text, or stdin.", file=sys.stderr)
        return False

    root_name = getattr(args, 'name', 'RootInterface')

    try:
        output = manager.generate(input_data, root_name=root_name)
    except ValueError as e:
        print(f"Error generating TypeScript code: {e}", file=sys.stderr)
        return False

    if getattr(args, 'output', None):
        try:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Code saved to {args.output}")
        except Exception as e:
            print(f"Error saving to file: {e}", file=sys.stderr)
            return False
    else:
        print(output)

    return True
