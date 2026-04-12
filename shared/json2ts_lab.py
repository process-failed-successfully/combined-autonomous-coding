import argparse
import json
import sys
from pathlib import Path

class Json2TsManager:
    """Manages conversion from JSON to TypeScript interfaces."""

    def convert(self, json_data: str, root_name: str = "RootObject") -> str:
        """Converts JSON string to TypeScript interfaces."""
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        interfaces = {}

        def _get_type(value, name):
            if isinstance(value, dict):
                # Title case for interface name, preserving existing camelCase
                # e.g., UserItem -> UserItem, user_item -> UserItem
                parts = [p for p in name.split('_') if p]
                if parts:
                    interface_name = "".join(p[0].upper() + p[1:] if len(p) > 0 else p for p in parts)
                else:
                    interface_name = name

                # Avoid root name collision or primitive names
                if not interface_name or interface_name.lower() in ("string", "number", "boolean", "any"):
                    interface_name = "Object"

                # generate interface
                _generate_interface(value, interface_name)
                return interface_name
            elif isinstance(value, list):
                if not value:
                    return "any[]"
                # get type of first element
                item_name = name + "Item" if name else "Item"
                if name.endswith("s") and len(name) > 1:
                    item_name = name[:-1] + "Item"
                item_type = _get_type(value[0], item_name)
                return f"{item_type}[]"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, bool):
                return "boolean"
            elif isinstance(value, (int, float)):
                return "number"
            elif value is None:
                return "any"
            else:
                return "any"

        def _generate_interface(obj: dict, name: str):
            if not isinstance(obj, dict):
                return

            # To avoid duplicates, check if it exists (very naive approach)
            original_name = name
            counter = 1
            while name in interfaces:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"export interface {name} {{"]
            for k, v in obj.items():
                prop_type = _get_type(v, k)
                # Simple property name check for spaces/invalid chars
                if not k.isidentifier():
                    lines.append(f"  \"{k}\": {prop_type};")
                else:
                    lines.append(f"  {k}: {prop_type};")
            lines.append("}")
            interfaces[name] = "\n".join(lines)

        if isinstance(data, dict):
            _generate_interface(data, root_name)
        elif isinstance(data, list):
            # If the root is a list, generate interface for the item and alias the root
            item_type = _get_type(data, root_name)
            return "\n\n".join(list(interfaces.values()) + [f"export type {root_name} = {item_type};"])
        else:
            return f"export type {root_name} = {_get_type(data, root_name)};"

        return "\n\n".join(reversed(list(interfaces.values())))


def run_json2ts_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Json2Ts Lab."""
    manager = Json2TsManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON to TS Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2ts")
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

    root_name = getattr(args, "name", "RootObject")

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
