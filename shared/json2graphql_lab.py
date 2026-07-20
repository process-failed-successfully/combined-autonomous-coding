import sys
import json
import argparse
from typing import Dict, Any, List

class Json2GraphQLManager:
    """Manager for converting JSON string to GraphQL type definitions."""

    def __init__(self):
        self.type_definitions = []
        self.type_names = set()

    def generate(self, json_str: str, root_name: str = "RootObject") -> str:
        self.type_definitions = []
        self.type_names = set()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                raise ValueError("JSON root must be an object or a list of objects.")

        self._parse_dict(data, root_name)

        # Child types are appended before parent types in _parse_dict
        return "\n\n".join(self.type_definitions)

    def _parse_dict(self, data: Dict[str, Any], type_name: str):
        original_type_name = type_name
        counter = 1
        while type_name in self.type_names:
            type_name = f"{original_type_name}{counter}"
            counter += 1

        self.type_names.add(type_name)

        fields = []
        for key, value in data.items():
            gql_type = self._infer_type(key, value)
            safe_key = self._sanitize_identifier(key)
            fields.append((safe_key, gql_type))

        type_def = f"type {type_name} {{\n"

        if not fields:
            # GraphQL types must have at least one field
            type_def += "  _empty: String\n"
        else:
            for name, type_str in fields:
                type_def += f"  {name}: {type_str}\n"

        type_def += "}"

        self.type_definitions.append(type_def)

    def _infer_type(self, key: str, value: Any) -> str:
        if value is None:
            return "String" # Fallback
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, list):
            if len(value) == 0:
                return "[String]" # Fallback
            else:
                first_elem = value[0]
                if isinstance(first_elem, dict):
                    child_type_name = self._to_pascal_case(key) + "Item"
                    if key.endswith("s") and len(key) > 1:
                        child_type_name = self._to_pascal_case(key[:-1]) + "Item"
                    self._parse_dict(first_elem, child_type_name)
                    return f"[{child_type_name}]"
                else:
                    item_type = self._infer_type(key, first_elem)
                    return f"[{item_type}]"
        elif isinstance(value, dict):
            child_type_name = self._to_pascal_case(key)
            self._parse_dict(value, child_type_name)
            return child_type_name
        else:
            return "String"

    def _to_pascal_case(self, s: str) -> str:
        # replace non-alphanumeric with space
        s = "".join([c if c.isalnum() else " " for c in s])
        words = s.split()
        if not words:
            return "NestedType"
        return "".join(w.capitalize() for w in words)

    def _sanitize_identifier(self, s: str) -> str:
        if not s:
            return "field"
        # replace non-alphanumeric with underscore
        s = "".join([c if c.isalnum() else "_" for c in s])
        # cannot start with number
        if s[0].isdigit():
            s = "_" + s
        return s

def run_json2graphql_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for the Json2GraphQL lab."""
    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to GraphQL Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2graphql")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return True

    manager = Json2GraphQLManager()

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

    root_name = getattr(args, 'name', 'RootObject')

    try:
        output = manager.generate(input_data, root_name=root_name)
    except ValueError as e:
        print(f"Error generating GraphQL code: {e}", file=sys.stderr)
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
