import argparse
import json
import sys
import re

class Json2KotlinManager:
    """Manages conversion from JSON to Kotlin data classes."""

    def __init__(self):
        self.classes = {}

    def _to_camel_case(self, s: str) -> str:
        if not s:
            return "nestedClass"
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "nestedClass"
        if len(words) == 1 and words[0][0].islower() and any(c.isupper() for c in words[0]):
            return words[0]
        return words[0].lower() + "".join(w.capitalize() for w in words[1:])

    def _to_pascal_case(self, s: str) -> str:
        if not s:
            return "NestedClass"
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)
        words = s.split()
        if not words:
            return "NestedClass"
        if len(words) == 1:
            return words[0][0].upper() + words[0][1:]
        return "".join(w.capitalize() for w in words)

    def convert(self, json_data: str, root_name: str = "RootClass", package_name: str = "com.example") -> str:
        """Converts JSON string to Kotlin data classes."""
        self.classes = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                class_name = self._to_pascal_case(name)
                if not class_name or class_name.lower() in ("string", "int", "double", "boolean", "any"):
                    class_name = "NestedClass"
                return _generate_class(value, class_name)
            elif isinstance(value, list):
                if not value:
                    return "List<Any>"
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
                return "Int"
            elif isinstance(value, float):
                return "Double"
            elif value is None:
                return "Any?"
            else:
                return "Any"

        def _generate_class(obj: dict, name: str):
            if not isinstance(obj, dict):
                return name

            original_name = name
            counter = 1
            while name in self.classes:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"data class {name}("]
            fields = []

            for i, (k, v) in enumerate(obj.items()):
                prop_type = _get_type(v, k)
                field_name = self._to_camel_case(k)
                if not field_name or field_name[0].isdigit():
                    field_name = "field" + field_name.capitalize()

                # Check for Kotlin reserved keywords
                kotlin_keywords = {"as", "break", "class", "continue", "do", "else", "false", "for", "fun", "if", "in", "interface", "is", "null", "object", "package", "return", "super", "this", "throw", "true", "try", "typealias", "typeof", "val", "var", "when", "while"}
                if field_name in kotlin_keywords:
                    field_name = f"`{field_name}`"

                annotation = ""
                if field_name.strip("`") != k or field_name.startswith("`"):
                    annotation = f"    @com.google.gson.annotations.SerializedName(\"{k}\")\n"

                comma = "," if i < len(obj) - 1 else ""
                lines.append(f"{annotation}    val {field_name}: {prop_type}{comma}")

            lines.append(")")
            self.classes[name] = "\n".join(lines)
            return name

        if isinstance(data, dict):
            _generate_class(data, root_name)
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
            self.classes["RootList"] = f"data class {root_name}List(val items: List<{item_type}>)"
        else:
            return f"// Root is a primitive type: typealias {root_name} = {_get_type(data, root_name)}"

        output = []
        if package_name:
            output.append(f"package {package_name}\n")

        for name, class_body in reversed(self.classes.items()):
            output.append(class_body)
            output.append("")

        return "\n".join(output).strip() + "\n"

def run_json2kotlin_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Kotlin Lab."""
    manager = Json2KotlinManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Kotlin Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2kotlin")
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

    root_name = getattr(args, "name", "RootClass")
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
