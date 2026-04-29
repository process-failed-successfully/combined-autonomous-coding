import argparse
import json
import sys

class Json2DartManager:
    """Manages conversion from JSON to Dart classes."""

    def __init__(self):
        self.classes = {}

    def _to_camel_case(self, s: str, first_upper: bool = False) -> str:
        if not s:
            return "NestedClass"

        import re
        s = re.sub(r'[^a-zA-Z0-9]', ' ', s)

        words = s.split()
        if not words:
            return "NestedClass"

        if first_upper:
            return "".join(w[0].upper() + w[1:] for w in words)
        else:
            return words[0][0].lower() + words[0][1:] + "".join(w[0].upper() + w[1:] for w in words[1:])

    def convert(self, json_data: str, root_name: str = "RootClass") -> str:
        """Converts JSON string to Dart classes."""
        self.classes = {}
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, name):
            if isinstance(value, dict):
                class_name = self._to_camel_case(name, first_upper=True)

                if not class_name or class_name.lower() in ("string", "double", "int", "bool", "dynamic"):
                    class_name = "Object"

                _generate_class(value, class_name)
                return class_name
            elif isinstance(value, list):
                if not value:
                    return "List<dynamic>"

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
                return "bool"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "double"
            elif value is None:
                return "dynamic"
            else:
                return "dynamic"

        def _generate_class(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            original_name = name
            counter = 1
            while name in self.classes:
                # To prevent overriding if we have similar names with different structures
                # (Simple approach: just create a new name)
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"class {name} {{"]

            # Fields
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                dart_field_name = self._to_camel_case(k)
                if not dart_field_name or dart_field_name[0].isdigit():
                    dart_field_name = "field" + dart_field_name.capitalize()

                # Make dynamic or nullable based on nullability logic, for MVP keep it simple
                # use nullable for all basic types except dynamic since dynamic is already nullable in Dart
                if prop_type != "dynamic":
                    lines.append(f"  {prop_type}? {dart_field_name};")
                else:
                    lines.append(f"  {prop_type} {dart_field_name};")

            lines.append("")

            # Constructor
            lines.append(f"  {name}({{")
            for k, v in obj.items():
                dart_field_name = self._to_camel_case(k)
                if not dart_field_name or dart_field_name[0].isdigit():
                    dart_field_name = "field" + dart_field_name.capitalize()
                lines.append(f"    this.{dart_field_name},")
            lines.append("  });")
            lines.append("")

            # fromJson
            lines.append(f"  factory {name}.fromJson(Map<String, dynamic> json) {{")
            lines.append(f"    return {name}(")
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                dart_field_name = self._to_camel_case(k)
                if not dart_field_name or dart_field_name[0].isdigit():
                    dart_field_name = "field" + dart_field_name.capitalize()

                if prop_type.startswith("List<"):
                    inner_type = prop_type[5:-1]
                    if inner_type in ("String", "int", "double", "bool", "dynamic"):
                        lines.append(f"      {dart_field_name}: json['{k}'] != null ? List<{inner_type}>.from(json['{k}']) : null,")
                    else:
                        lines.append(f"      {dart_field_name}: json['{k}'] != null ? (json['{k}'] as List).map((i) => {inner_type}.fromJson(i)).toList() : null,")
                elif prop_type not in ("String", "int", "double", "bool", "dynamic"):
                    lines.append(f"      {dart_field_name}: json['{k}'] != null ? {prop_type}.fromJson(json['{k}']) : null,")
                else:
                    lines.append(f"      {dart_field_name}: json['{k}'],")
            lines.append("    );")
            lines.append("  }")
            lines.append("")

            # toJson
            lines.append("  Map<String, dynamic> toJson() {")
            lines.append("    final Map<String, dynamic> data = <String, dynamic>{};")
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                dart_field_name = self._to_camel_case(k)
                if not dart_field_name or dart_field_name[0].isdigit():
                    dart_field_name = "field" + dart_field_name.capitalize()

                if prop_type.startswith("List<"):
                    inner_type = prop_type[5:-1]
                    if inner_type in ("String", "int", "double", "bool", "dynamic"):
                        lines.append(f"    data['{k}'] = this.{dart_field_name};")
                    else:
                        lines.append(f"    if (this.{dart_field_name} != null) {{")
                        lines.append(f"      data['{k}'] = this.{dart_field_name}!.map((v) => v.toJson()).toList();")
                        lines.append(f"    }}")
                elif prop_type not in ("String", "int", "double", "bool", "dynamic"):
                    lines.append(f"    if (this.{dart_field_name} != null) {{")
                    lines.append(f"      data['{k}'] = this.{dart_field_name}!.toJson();")
                    lines.append(f"    }}")
                else:
                    lines.append(f"    data['{k}'] = this.{dart_field_name};")
            lines.append("    return data;")
            lines.append("  }")

            lines.append("}")
            self.classes[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_class(data, root_name)
        elif isinstance(data, list):
            item_type = _get_type(data, root_name)
            if item_type in self.classes:
                pass
            return "\n\n".join(list(self.classes.values()))
        else:
            return f"// Unsupported root type: {type(data)}"

        return "\n\n".join(list(self.classes.values()))


def run_json2dart_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Dart Lab."""
    manager = Json2DartManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Dart Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2dart")
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

    root_name = getattr(args, "name", "RootClass")

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
