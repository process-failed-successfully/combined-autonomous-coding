import argparse
import json
import sys

class Json2SwiftManager:
    """Manages conversion from JSON to Swift structs."""

    def __init__(self):
        self.structs = {}

    def _to_camel_case(self, s: str, first_upper: bool = False) -> str:
        if not s:
            return "NestedStruct"

        import re
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)

        words = s.split()
        if not words:
            return "NestedStruct"

        if first_upper:
            return "".join(w[0].upper() + w[1:] for w in words)
        else:
            return words[0][0].lower() + words[0][1:] + "".join(w[0].upper() + w[1:] for w in words[1:])

    def convert(self, json_data: str, root_name: str = "RootStruct") -> str:
        """Converts JSON string to Swift structs."""
        self.structs = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                struct_name = self._to_camel_case(name, first_upper=True)

                if not struct_name or struct_name.lower() in ("string", "double", "int", "bool", "any"):
                    struct_name = "Any"

                _generate_struct(value, struct_name)
                return struct_name
            elif isinstance(value, list):
                if not value:
                    return "[Any]"

                item_name = name
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1]
                elif name.endswith("List") and len(name) > 4:
                    item_name = name[:-4]

                item_type = _get_type(value[0], item_name)
                return f"[{item_type}]"
            elif isinstance(value, str):
                return "String"
            elif isinstance(value, bool):
                return "Bool"
            elif isinstance(value, int):
                return "Int"
            elif isinstance(value, float):
                return "Double"
            elif value is None:
                return "Any"
            else:
                return "Any"

        def _generate_struct(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.structs:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"struct {name}: Codable {{"]

            for k, v in obj.items():
                prop_type = _get_type(v, k)
                swift_field_name = self._to_camel_case(k)
                if not swift_field_name or swift_field_name[0].isdigit():
                    swift_field_name = "field" + swift_field_name.capitalize()

                # Use optional for properties
                if prop_type == "Any" or prop_type == "[Any]":
                    # Codable doesn't support Any directly out of the box without custom implementation
                    # So we use a basic fallback
                    pass # We will output it as is, usually user needs to adapt it

                # if the original key is different from camelCase, we need CodingKeys
                lines.append(f"    var {swift_field_name}: {prop_type}?")

            # Add CodingKeys if necessary
            needs_coding_keys = any(self._to_camel_case(k) != k for k in obj.keys())
            if needs_coding_keys:
                lines.append("")
                lines.append("    enum CodingKeys: String, CodingKey {")
                for k in obj.keys():
                    swift_field_name = self._to_camel_case(k)
                    if not swift_field_name or swift_field_name[0].isdigit():
                        swift_field_name = "field" + swift_field_name.capitalize()

                    if swift_field_name != k:
                        lines.append(f"        case {swift_field_name} = \"{k}\"")
                    else:
                        lines.append(f"        case {swift_field_name}")
                lines.append("    }")

            lines.append("}")
            self.structs[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_struct(data, root_name)
        elif isinstance(data, list):
            item_type = _get_type(data, root_name)
            if item_type in self.structs:
                pass
            return "\n\n".join(list(self.structs.values()))
        else:
            return f"// Unsupported root type: {type(data)}"

        # Reverse list so dependencies come first usually
        return "\n\n".join(reversed(list(self.structs.values())))


def run_json2swift_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Swift Lab."""
    manager = Json2SwiftManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Swift Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2swift")
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
