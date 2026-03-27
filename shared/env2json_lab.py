import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


class Env2JsonManager:
    """Manages conversion between .env format and JSON."""

    def env_to_json(self, env_content: str) -> Dict[str, Any]:
        """Converts .env string to a JSON object (dict)."""
        result = {}
        for line in env_content.splitlines():
            line = line.strip()
            # Ignore empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Split by first '='
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Handle quotes
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                result[key] = value

        return result

    def json_to_env(self, json_content: str) -> str:
        """Converts JSON string to .env format string."""
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ValueError("JSON input must be an object (dict) to convert to .env format.")

        lines = []
        for key, value in data.items():
            if value is None:
                value_str = ""
            elif isinstance(value, (dict, list)):
                # Serialize complex types back to JSON string
                value_str = json.dumps(value)
            else:
                value_str = str(value)

            # Add quotes if the string contains spaces or special characters
            if ' ' in value_str or '#' in value_str or '=' in value_str:
                # Escape existing double quotes if we wrap in double quotes
                value_str = value_str.replace('"', '\\"')
                value_str = f'"{value_str}"'

            lines.append(f"{key}={value_str}")

        return "\n".join(lines)


def run_env2json_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for env2json lab."""
    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching Env to JSON Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-env2json")
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

    manager = Env2JsonManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File '{filepath}' not found.", file=sys.stderr)
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
            return False

        input_text = content
    elif getattr(args, "text", None):
        input_text = args.text
    else:
        print("Error: Either --file or --text must be provided.", file=sys.stderr)
        return False

    output_path = Path(args.output) if getattr(args, "output", None) else None

    # Determine direction based on command or infer from content
    action = getattr(args, "action", "env2json")  # default direction
    if hasattr(args, "command") and args.command in ["json2env-lab", "json2env"]:
        action = "json2env"

    try:
        if action == "json2env":
            result = manager.json_to_env(input_text)
        else:
            data = manager.env_to_json(input_text)
            result = json.dumps(data, indent=2)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Output written to {output_path}")
        else:
            print(result)
        return True
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
