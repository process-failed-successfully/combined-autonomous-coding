import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Set

class Json2TsManager:
    """Manages the conversion of JSON data to TypeScript interfaces."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def _capitalize(self, s: str) -> str:
        if not s:
            return s
        return s[0].upper() + s[1:]

    def _parse_type(self, value: Any, key: str, interfaces: Dict[str, str]) -> str:
        if value is None:
            return "any"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int) or isinstance(value, float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            if len(value) == 0:
                return "any[]"
            # Get the type of the first element (assuming homogeneous list)
            elem_type = self._parse_type(value[0], key, interfaces)
            return f"{elem_type}[]"
        if isinstance(value, dict):
            # Nested object: create a new interface
            interface_name = self._capitalize(key)
            self._generate_interface(interface_name, value, interfaces)
            return interface_name
        return "any"

    def _generate_interface(self, name: str, data: Dict[str, Any], interfaces: Dict[str, str]):
        if name in interfaces:
            # Simple collision avoidance (very basic)
            return

        lines = []
        lines.append(f"export interface {name} {{")
        for k, v in data.items():
            ts_type = self._parse_type(v, k, interfaces)
            # Add ? if value is null maybe, but for simplicity let's just use strict or make all optional?
            # Let's make it strict based on the object instance.
            safe_k = k if k.isalnum() else f'"{k}"'
            lines.append(f"  {safe_k}: {ts_type};")
        lines.append("}")

        interfaces[name] = "\n".join(lines)

    def convert(self, json_data: str, root_name: str = "Root") -> str:
        """Converts a JSON string to TypeScript interfaces."""
        if not json_data or not json_data.strip():
            return ""

        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}"

        interfaces: Dict[str, str] = {}

        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                self._generate_interface(root_name, data[0], interfaces)
            else:
                return f"// Expected an array of objects or an object. Got an array of primitives."
        elif isinstance(data, dict):
            self._generate_interface(root_name, data, interfaces)
        else:
            return "// Expected JSON object or array of objects."

        # Return interfaces in reverse order of creation so root is at the bottom (or top)
        # Actually top is fine.
        # But we need to define convert such that the string is parsed.
        # However, Python 3.8+ dicts preserve insertion order. Let's reverse them so that
        # dependencies (nested interfaces) appear before the root interface.
        return "\n\n".join(reversed(list(interfaces.values())))

def run_json2ts_lab_logic(args) -> bool:
    """CLI handler for JSON to TypeScript conversion."""
    manager = Json2TsManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
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

    content = None
    if getattr(args, "file", None):
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File {args.file} not found.", file=sys.stderr)
            return False
        content = path.read_text(encoding="utf-8", errors="replace")
    elif getattr(args, "text", None):
        content = args.text
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()
        else:
            print("Error: Input required via --file, --text, or stdin.", file=sys.stderr)
            return False

    root_name = getattr(args, "name", "Root")
    ts_output = manager.convert(content, root_name=root_name)

    if getattr(args, "output", None):
        path = Path(args.output)
        path.write_text(ts_output, encoding="utf-8")
        print(f"✅ Saved TS to {args.output}")
    else:
        print(ts_output)

    return True
