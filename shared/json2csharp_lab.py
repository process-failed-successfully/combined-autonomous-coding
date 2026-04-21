import argparse
import json
import sys
import re

class Json2CSharpManager:
    """Manages conversion from JSON to C# classes."""

    def __init__(self):
        self.classes = {}

    def _to_pascal_case(self, s: str) -> str:
        if not s:
            return "NestedClass"
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "NestedClass"
        return "".join(w[0].upper() + w[1:] for w in words if w)

    def convert(self, json_data: str, root_name: str = "RootClass", namespace: str = "MyNamespace") -> str:
        """Converts JSON string to C# classes."""
        self.classes = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                class_name = self._to_pascal_case(name)
                if not class_name or class_name.lower() in ("string", "int", "double", "bool", "object"):
                    class_name = "NestedClass"
                _generate_class(value, class_name)
                return class_name
            elif isinstance(value, list):
                if not value:
                    return "List<object>"
                item_name = name
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1]
                elif name.endswith("List") and len(name) > 4:
                    item_name = name[:-4]
                item_type = _get_type(value[0], item_name)
                return f"List<{item_type}>"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "double"
            elif value is None:
                return "object"
            else:
                return "object"

        def _generate_class(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.classes:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"    public class {name}\n    {{"]
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                cs_field_name = self._to_pascal_case(k)
                if not cs_field_name or cs_field_name[0].isdigit():
                    cs_field_name = "Field" + cs_field_name

                # Add JsonProperty if the original JSON key differs from the C# property name
                if k != cs_field_name:
                    lines.append(f'        [JsonProperty("{k}")]')

                lines.append(f"        public {prop_type} {cs_field_name} {{ get; set; }}")

            lines.append("    }")
            self.classes[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_class(data, root_name)
        elif isinstance(data, list):
            # Pass data[0] instead of data to _get_type to get the item type
            if not data:
                item_type = "object"
            else:
                item_type = _get_type(data[0], root_name)
            self.classes["RootList"] = f"    public class {root_name}List\n    {{\n        public List<{item_type}> Items {{ get; set; }}\n    }}"
        else:
            return f"// Root is a primitive type: {_get_type(data, root_name)}"

        output = []
        output.append("using System;")
        output.append("using System.Collections.Generic;")
        output.append("using Newtonsoft.Json;")
        output.append("")
        if namespace:
            output.append(f"namespace {namespace}\n{{")

        # Output dependencies first, then root class
        for name, class_body in reversed(self.classes.items()):
            output.append(class_body)
            output.append("")

        if namespace:
            output.append("}")

        return "\n".join(output)

def run_json2csharp_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2CSharp Lab."""
    manager = Json2CSharpManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to C# Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2csharp")
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
    elif getattr(args, "text", None) is not None: # check is not None to handle empty string
        input_data = args.text
    else:
        if not sys.stdin.isatty():
            try:
                input_data = sys.stdin.read()
            except OSError:
                # Handle pytest stdin capture error
                input_data = ""
        else:
            print("Error: No input provided. Use --file, --text, or pipe via stdin.", file=sys.stderr)
            return False

    if not input_data.strip():
        print("Error: Empty input data.", file=sys.stderr)
        return False

    root_name = getattr(args, "name", "RootClass")
    namespace = getattr(args, "namespace", "MyNamespace")

    try:
        result = manager.convert(input_data, root_name, namespace)
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
