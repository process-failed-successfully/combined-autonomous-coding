import argparse
import json
import sys
import re

class Json2RustManager:
    """Manages conversion from JSON to Rust structs."""

    def __init__(self):
        self.structs = {}

    def _to_camel_case(self, s: str) -> str:
        if not s:
            return "NestedStruct"

        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "NestedStruct"

        result = "".join(w[0].upper() + w[1:] for w in words)
        return result

    def _to_snake_case(self, s: str) -> str:
        if not s:
            return "nested_struct"
        s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
        s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
        s = re.sub(r'[^a-zA-Z0-9]', '_', s)
        return s.lower()

    def convert(self, json_data: str, root_name: str = "RootStruct") -> str:
        """Converts JSON string to Rust structs."""
        self.structs = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                struct_name = self._to_camel_case(name)

                # Avoid empty names or primitive names
                if not struct_name or struct_name.lower() in ("string", "f64", "i64", "bool", "any", "value"):
                    struct_name = "Object"

                _generate_struct(value, struct_name)
                return struct_name
            elif isinstance(value, list):
                if not value:
                    return "Vec<serde_json::Value>"

                item_name = name
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1]
                elif name.endswith("List") and len(name) > 4:
                    item_name = name[:-4]

                item_type = _get_type(value[0], item_name)
                return f"Vec<{item_type}>"
            elif isinstance(value, str):
                return "String"
            elif isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "i64"
            elif isinstance(value, float):
                return "f64"
            elif value is None:
                return "Option<serde_json::Value>"
            else:
                return "serde_json::Value"

        def _generate_struct(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.structs:
                name = f"{original_name}{counter}"
                counter += 1

            lines = ["#[derive(Default, Debug, Clone, PartialEq, serde::Serialize, serde::Deserialize)]"]
            # To handle serde default configuration we can assume CamelCase or just let it rename
            lines.append(f"#[serde(rename_all = \"camelCase\")]")
            lines.append(f"pub struct {name} {{")
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                rust_field_name = self._to_snake_case(k)
                if not rust_field_name or rust_field_name[0].isdigit():
                    rust_field_name = "field_" + rust_field_name

                # Check for Rust reserved keywords
                rust_keywords = {"as", "break", "const", "continue", "crate", "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in", "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return", "self", "Self", "static", "struct", "super", "trait", "true", "type", "unsafe", "use", "where", "while", "async", "await", "dyn", "abstract", "become", "box", "do", "final", "macro", "override", "priv", "typeof", "unsized", "virtual", "yield", "try"}

                rename_attr = ""
                # If the property name is not snake_case or is a keyword we should output `#[serde(rename = "k")]`
                # However, since we have rename_all = "camelCase", we only need to rename if the field name differs from camelCase transformation or is a keyword
                if rust_field_name in rust_keywords:
                    rust_field_name = f"r#{rust_field_name}"

                if self._to_camel_case(k) != self._to_camel_case(rust_field_name) or rust_field_name.startswith("r#"):
                     rename_attr = f"\t#[serde(rename = \"{k}\")]\n"

                lines.append(f"{rename_attr}\tpub {rust_field_name}: {prop_type},")
            lines.append("}")
            self.structs[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_struct(data, root_name)
        elif isinstance(data, list):
            item_type = _get_type(data, root_name)
            return "\n\n".join(list(self.structs.values()) + [f"pub type {root_name} = {item_type};"])
        else:
            return f"pub type {root_name} = {_get_type(data, root_name)};"

        return "\n\n".join(reversed(list(self.structs.values())))

def run_json2rust_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Rust Lab."""
    manager = Json2RustManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Rust Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2rust")
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
