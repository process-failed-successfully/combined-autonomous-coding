import argparse
import json
import sys

class Json2GoManager:
    """Manages conversion from JSON to Go structs."""

    def __init__(self):
        self.structs = {}

    def _to_camel_case(self, s: str) -> str:
        if not s:
            return "NestedStruct"

        # We need to preserve camelCase of original field or split by non-alphanumeric
        # For simplicity, let's replace non-alphanumeric with spaces, then title case each word
        # But if it's already camelCase like 'isActive', we want 'IsActive'.
        # Let's split by non-alphanumeric or underscores
        import re
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)

        # Split by space
        words = s.split()
        if not words:
            return "NestedStruct"

        # For each word, just capitalize the first letter, leave rest intact (handles 'isActive' -> 'IsActive', 'name' -> 'Name')
        result = "".join(w[0].upper() + w[1:] for w in words)
        return result

    def convert(self, json_data: str, root_name: str = "RootStruct") -> str:
        """Converts JSON string to Go structs."""
        self.structs = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                struct_name = self._to_camel_case(name)

                # Avoid empty names or primitive names
                if not struct_name or struct_name.lower() in ("string", "float64", "int", "bool", "any", "interface{}"):
                    struct_name = "Object"

                _generate_struct(value, struct_name)
                return f"*{struct_name}"
            elif isinstance(value, list):
                if not value:
                    return "[]interface{}"

                item_name = name
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1]
                elif name.endswith("List") and len(name) > 4:
                    item_name = name[:-4]

                item_type = _get_type(value[0], item_name)
                return f"[]{item_type}"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float64"
            elif value is None:
                return "interface{}"
            else:
                return "interface{}"

        def _generate_struct(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.structs:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"type {name} struct {{"]
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                go_field_name = self._to_camel_case(k)
                if not go_field_name or go_field_name[0].isdigit():
                    go_field_name = "Field" + go_field_name

                json_tag = f'`json:"{k}"`'
                lines.append(f"\t{go_field_name} {prop_type} {json_tag}")
            lines.append("}")
            self.structs[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_struct(data, root_name)
        elif isinstance(data, list):
            item_type = _get_type(data, root_name)
            return "\n\n".join(list(self.structs.values()) + [f"type {root_name} {item_type}"])
        else:
            return f"type {root_name} {_get_type(data, root_name)}"

        # Return structs in reverse order so dependencies appear first if possible
        return "\n\n".join(reversed(list(self.structs.values())))


def run_json2go_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Go Lab."""
    manager = Json2GoManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Go Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2go")
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

    input_data = ""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                input_data = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        input_data = args.text
    else:
        # read from stdin
        if not sys.stdin.isatty():
            input_data = sys.stdin.read()
        else:
            print("Error: No input provided. Use --file, --text, or pipe via stdin.", file=sys.stderr)
            return False

    if not input_data.strip():
        print("Error: Empty input data.", file=sys.stderr)
        return False

    root_name = getattr(args, "name", "RootStruct")

    try:
        result = manager.convert(input_data, root_name)
        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Output written to {args.output}")
        else:
            print(result)
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
