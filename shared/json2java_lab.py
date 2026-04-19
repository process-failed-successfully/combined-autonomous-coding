import argparse
import json
import sys

class Json2JavaManager:
    """Manages conversion from JSON to Java classes."""

    def __init__(self):
        self.classes = {}

    def _to_camel_case(self, s: str) -> str:
        if not s:
            return "nestedObject"
        import re
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "nestedObject"
        # Preserve original camelCase if possible, or build camelCase
        if len(words) == 1 and words[0][0].islower() and any(c.isupper() for c in words[0]):
            return words[0] # Return as is for things like 'isActive'
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def _to_pascal_case(self, s: str) -> str:
        if not s:
            return "NestedObject"
        import re
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "NestedObject"
        # If the whole string is basically just camel case, just capitalize first letter
        if len(words) == 1:
            return words[0][0].upper() + words[0][1:]
        return "".join(w.capitalize() for w in words)

    def convert(self, json_data: str, root_name: str = "RootObject", package_name: str = "com.example") -> str:
        """Converts JSON string to Java classes."""
        self.classes = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                class_name = self._to_pascal_case(name)
                if not class_name or class_name.lower() in ("string", "integer", "double", "boolean", "object"):
                    class_name = "NestedObject"
                _generate_class(value, class_name)
                return class_name
            elif isinstance(value, list):
                if not value:
                    return "List<Object>"
                item_name = name
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1]
                elif name.endswith("List") and len(name) > 4:
                    item_name = name[:-4]
                item_type = _get_type(value[0], item_name)
                return f"List<{item_type}>"
            elif isinstance(value, str):
                return "String"
            elif isinstance(value, bool):
                return "Boolean"
            elif isinstance(value, int):
                return "Integer"
            elif isinstance(value, float):
                return "Double"
            elif value is None:
                return "Object"
            else:
                return "Object"

        def _generate_class(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.classes:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"public class {name} {{"]
            fields = []

            for k, v in obj.items():
                prop_type = _get_type(v, k)
                field_name = self._to_camel_case(k)
                if not field_name or field_name[0].isdigit():
                    field_name = "field" + field_name.capitalize()

                # Use Jackson annotation
                lines.append(f'    @com.fasterxml.jackson.annotation.JsonProperty("{k}")')
                lines.append(f"    private {prop_type} {field_name};")
                fields.append((prop_type, field_name))

            lines.append("")

            # Generate getters and setters
            for prop_type, field_name in fields:
                capitalized = field_name[0].upper() + field_name[1:]
                # Getter
                lines.append(f"    public {prop_type} get{capitalized}() {{")
                lines.append(f"        return {field_name};")
                lines.append("    }")
                # Setter
                lines.append(f"    public void set{capitalized}({prop_type} {field_name}) {{")
                lines.append(f"        this.{field_name} = {field_name};")
                lines.append("    }")

            lines.append("}")
            self.classes[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_class(data, root_name)
        elif isinstance(data, list):
            # Evaluate the item inside the list directly, not the list itself
            if not data:
                item_type = "Object"
            else:
                item_name = root_name
                if root_name.endswith("s") and len(root_name) > 1:
                    item_name = root_name[:-1]
                elif root_name.endswith("List") and len(root_name) > 4:
                    item_name = root_name[:-4]
                item_type = _get_type(data[0], item_name)
            self.classes["RootList"] = f"public class {root_name}List {{\n    private List<{item_type}> items;\n    public List<{item_type}> getItems() {{\n        return items;\n    }}\n    public void setItems(List<{item_type}> items) {{\n        this.items = items;\n    }}\n}}"
        else:
            return f"// Root is a primitive type: {_get_type(data, root_name)}"

        output = []
        if package_name:
            output.append(f"package {package_name};\n")
        output.append("import java.util.List;\n")

        # Output dependencies first, then root class
        for name, class_body in reversed(self.classes.items()):
            output.append(class_body)
            output.append("")

        return "\n".join(output)

def run_json2java_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Java Lab."""
    manager = Json2JavaManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Java Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2java")
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

    root_name = getattr(args, "name", "RootObject")
    package_name = getattr(args, "package", "com.example")

    try:
        result = manager.convert(input_data, root_name, package_name)
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
