import argparse
import json
import sys


class Json2JavaManager:
    """Manages conversion from JSON to Java classes."""

    def __init__(self):
        self.classes = {}

    def _to_camel_case(self, s: str, capitalize_first: bool = False) -> str:
        if not s:
            return "NestedClass" if capitalize_first else "nestedClass"

        import re
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)

        words = s.split()
        if not words:
            return "NestedClass" if capitalize_first else "nestedClass"

        result = ""
        for i, w in enumerate(words):
            if i == 0 and not capitalize_first:
                result += w[0].lower() + w[1:]
            else:
                result += w[0].upper() + w[1:]
        return result

    def convert(self, json_data: str, root_name: str = "RootObject", package_name: str = "") -> str:
        """Converts JSON string to Java classes."""
        self.classes = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                class_name = self._to_camel_case(name, capitalize_first=True)

                if not class_name or class_name.lower() in ("string", "double", "int", "boolean", "object"):
                    class_name = "Object"

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
                return "boolean"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "double"
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

            lines = []
            lines.append(f"public class {name} {{")

            fields = []

            for k, v in obj.items():
                prop_type = _get_type(v, k)
                java_field_name = self._to_camel_case(k)
                if not java_field_name or java_field_name[0].isdigit():
                    java_field_name = "field" + java_field_name.capitalize()

                if k != java_field_name:
                    lines.append(f"    @com.fasterxml.jackson.annotation.JsonProperty(\"{k}\")")
                lines.append(f"    private {prop_type} {java_field_name};")
                fields.append((prop_type, java_field_name))

            lines.append("")

            # Generate getters and setters
            for prop_type, field_name in fields:
                capitalized_name = field_name[0].upper() + field_name[1:]

                # Getter
                prefix = "is" if prop_type == "boolean" else "get"
                lines.append(f"    public {prop_type} {prefix}{capitalized_name}() {{")
                lines.append(f"        return {field_name};")
                lines.append("    }")
                lines.append("")

                # Setter
                lines.append(f"    public void set{capitalized_name}({prop_type} {field_name}) {{")
                lines.append(f"        this.{field_name} = {field_name};")
                lines.append("    }")
                lines.append("")

            lines.append("}")
            self.classes[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_class(data, root_name)
        elif isinstance(data, list):
            item_type = _get_type(data, root_name)
            self.classes["RootWrapper"] = "public class RootWrapper {\n    private " + item_type + " items;\n}"

        output_lines = []
        if package_name:
            output_lines.append(f"package {package_name};")
            output_lines.append("")

        has_list = any("List<" in content for content in self.classes.values())
        if has_list:
            output_lines.append("import java.util.List;")
            output_lines.append("")

        output_lines.extend(reversed(list(self.classes.values())))

        return "\n\n".join(output_lines)


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
    package_name = getattr(args, "package", "")

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
