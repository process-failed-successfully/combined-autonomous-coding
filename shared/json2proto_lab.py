import argparse
import json
import sys
import re

class Json2ProtoManager:
    """Manages conversion from JSON to Protobuf messages."""

    def __init__(self):
        self.messages = {}

    def _to_pascal_case(self, s: str) -> str:
        if not s:
            return "NestedMessage"
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "NestedMessage"
        return "".join(w[0].upper() + w[1:] for w in words)

    def _to_snake_case(self, s: str) -> str:
        if not s:
            return "field"
        s = re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()
        s = re.sub(r'[^a-z0-9_]', '_', s)
        return s

    def convert(self, json_data: str, root_name: str = "RootMessage") -> str:
        """Converts JSON string to Protobuf schema."""
        self.messages = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                msg_name = self._to_pascal_case(name)
                if not msg_name or msg_name.lower() in ("string", "double", "int64", "bool", "any"):
                    msg_name = "ObjectMessage"
                _generate_message(value, msg_name)
                return msg_name
            elif isinstance(value, list):
                if not value:
                    return "repeated string"

                item_name = name
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1]
                elif name.endswith("List") and len(name) > 4:
                    item_name = name[:-4]

                item_type = _get_type(value[0], item_name)
                if item_type.startswith("repeated "):
                    return item_type # Protobuf does not support multidimensional arrays easily
                return f"repeated {item_type}"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "int64"
            elif isinstance(value, float):
                return "double"
            elif value is None:
                return "string"
            else:
                return "string"

        def _generate_message(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.messages:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"message {name} {{"]
            field_idx = 1
            for k, v in obj.items():
                prop_type = _get_type(v, k)

                proto_field_name = self._to_snake_case(k)
                if not proto_field_name or proto_field_name[0].isdigit():
                    proto_field_name = "field_" + proto_field_name

                lines.append(f"  {prop_type} {proto_field_name} = {field_idx};")
                field_idx += 1
            lines.append("}")
            self.messages[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_message(data, root_name)
        elif isinstance(data, list):
            item_type = _get_type(data, root_name)
            if item_type.startswith("repeated "):
                item_type = item_type.replace("repeated ", "")
            self.messages[root_name] = f"message {root_name} {{\n  repeated {item_type} items = 1;\n}}"
        else:
            return f"// Root is a primitive type: {_get_type(data, root_name)}"

        res = 'syntax = "proto3";\n\n'
        res += "\n\n".join(reversed(list(self.messages.values())))
        return res


def run_json2proto_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Proto Lab."""
    manager = Json2ProtoManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Protobuf Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2proto")
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

    root_name = getattr(args, "name", "RootMessage")

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
