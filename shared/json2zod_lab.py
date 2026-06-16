import argparse
import json
import sys

class Json2ZodManager:
    """Manages conversion from JSON to TypeScript Zod schemas."""

    def convert(self, json_data: str, root_name: str = "Schema") -> str:
        """Converts JSON string to TypeScript Zod schemas."""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        def _get_type(value, indent_level=1):
            indent = "  " * indent_level
            if isinstance(value, dict):
                lines = ["z.object({"]
                for k, v in value.items():
                    prop_type = _get_type(v, indent_level + 1)
                    if not k.isidentifier():
                        lines.append(f"{indent}  \"{k}\": {prop_type},")
                    else:
                        lines.append(f"{indent}  {k}: {prop_type},")
                lines.append(f"{indent}}})")
                return "\n".join(lines)
            elif isinstance(value, list):
                if not value:
                    return "z.array(z.any())"
                item_type = _get_type(value[0], indent_level)
                # For single-line items like z.string(), keep it inline.
                # If the item_type has newlines (e.g. z.object), it handles its own indent.
                if "\n" in item_type:
                    return f"z.array(\n{indent}  {item_type}\n{indent})"
                else:
                    return f"z.array({item_type})"
            elif isinstance(value, str):
                return "z.string()"
            elif isinstance(value, bool):
                return "z.boolean()"
            elif isinstance(value, (int, float)):
                return "z.number()"
            elif value is None:
                return "z.any()"
            else:
                return "z.any()"

        imports = "import { z } from \"zod\";\n\n"
        schema_type = _get_type(data, 0)

        return f"{imports}export const {root_name} = {schema_type};\n\nexport type {root_name}Type = z.infer<typeof {root_name}>;"


def run_json2zod_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Zod Lab."""
    manager = Json2ZodManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to Zod Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2zod")
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

    root_name = getattr(args, "name", "Schema")

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
