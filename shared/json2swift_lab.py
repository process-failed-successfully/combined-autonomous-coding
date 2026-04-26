import argparse
import json
import sys
import re

class Json2SwiftManager:
    """Manages conversion from JSON to Swift structs."""

    def __init__(self):
        self.structs = {}

    def _to_camel_case(self, s: str) -> str:
        if not s:
            return "nestedStruct"
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "nestedStruct"
        if len(words) == 1 and words[0][0].islower() and any(c.isupper() for c in words[0]):
            return words[0]
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def _to_pascal_case(self, s: str) -> str:
        if not s:
            return "NestedStruct"
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "NestedStruct"
        if len(words) == 1:
            return words[0][0].upper() + words[0][1:]
        return "".join(w.capitalize() for w in words)

    def convert(self, json_data: str, root_name: str = "RootStruct") -> str:
        """Converts JSON string to Swift structs."""
        self.structs = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                struct_name = self._to_pascal_case(name)
                if not struct_name or struct_name.lower() in ("string", "int", "double", "bool", "any"):
                    struct_name = "NestedStruct"
                return _generate_struct(value, struct_name)
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
                return "Any?"
            else:
                return "Any"

        def _generate_struct(obj: dict, name: str):
            if not isinstance(obj, dict):
                return name

            original_name = name
            counter = 1
            while name in self.structs:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"struct {name}: Codable {{"]
            fields = []

            for k, v in obj.items():
                prop_type = _get_type(v, k)
                field_name = self._to_camel_case(k)
                if not field_name or field_name[0].isdigit():
                    field_name = "field" + field_name.capitalize()

                # Check for Swift reserved keywords
                swift_keywords = {"class", "deinit", "enum", "extension", "func", "import", "init", "inout", "let", "protocol", "struct", "subscript", "typealias", "var", "break", "case", "continue", "default", "defer", "do", "else", "fallthrough", "for", "guard", "if", "in", "repeat", "return", "switch", "where", "while", "as", "Any", "catch", "false", "is", "nil", "rethrows", "super", "self", "Self", "throw", "throws", "true", "try", "_"}
                if field_name in swift_keywords:
                    field_name = f"`{field_name}`"

                # Check if we need CodingKeys (only if field name changed or is different from JSON key)
                needs_coding_keys = field_name.strip("`") != k or field_name.startswith("`")
                fields.append((field_name, prop_type, k, needs_coding_keys))

                lines.append(f"    let {field_name}: {prop_type}?")

            any_needs_coding_keys = any(f[3] for f in fields)
            if any_needs_coding_keys:
                lines.append("")
                lines.append("    enum CodingKeys: String, CodingKey {")
                for field_name, _, k, needs_coding_keys in fields:
                    if needs_coding_keys:
                        lines.append(f"        case {field_name} = \"{k}\"")
                    else:
                        lines.append(f"        case {field_name}")
                lines.append("    }")

            lines.append("}")
            self.structs[name] = "\n".join(lines)
            return name

        if isinstance(data, dict):
            _generate_struct(data, root_name)
        elif isinstance(data, list):
            if not data:
                item_type = "Any"
            else:
                item_name = root_name
                if root_name.endswith("s") and len(root_name) > 1:
                    item_name = root_name[:-1]
                elif root_name.endswith("List") and len(root_name) > 4:
                    item_name = root_name[:-4]
                item_type = _get_type(data[0], item_name)
            self.structs["RootStructList"] = f"struct {root_name}List: Codable {{\n    let items: [{item_type}]?\n}}"
        else:
            return f"// Root is a primitive type\ntypealias {root_name} = {_get_type(data, root_name)}"

        output = []
        for name, struct_body in reversed(self.structs.items()):
            output.append(struct_body)
            output.append("")

        return "import Foundation\n\n" + "\n".join(output).strip() + "\n"

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
