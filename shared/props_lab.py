import argparse
import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any


class PropsLabManager:
    """Manages conversion between Java .properties files and JSON/YAML formats."""

    def props_to_dict(self, props_content: str) -> Dict[str, Any]:
        """Converts Java .properties string to a dictionary."""
        result = {}
        for line in props_content.splitlines():
            line = line.strip()
            # Ignore empty lines and comments
            if not line or line.startswith('#') or line.startswith('!'):
                continue

            # Split by first '=' or ':' (simplistic parser)
            separator = '='
            if '=' not in line and ':' in line:
                separator = ':'

            if separator in line:
                key, value = line.split(separator, 1)
                key = key.strip()
                value = value.strip()
                result[key] = value

        return result

    def dict_to_props(self, data: Dict[str, Any]) -> str:
        """Converts a dictionary to a Java .properties format string."""
        lines = []
        # simple flattening for dict-to-props (assuming shallow dict or basic depth)

        def flatten_dict(d, parent_key='', sep='.'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)

        flat_data = flatten_dict(data)

        for key, value in flat_data.items():
            if value is None:
                value_str = ""
            else:
                value_str = str(value)

            lines.append(f"{key}={value_str}")

        return "\n".join(lines)


    def props2json(self, props_content: str) -> str:
        data = self.props_to_dict(props_content)
        return json.dumps(data, indent=2)

    def json2props(self, json_content: str) -> str:
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ValueError("JSON input must be an object (dict) to convert to .properties format.")

        return self.dict_to_props(data)

    def props2yaml(self, props_content: str) -> str:
        data = self.props_to_dict(props_content)
        return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)

    def yaml2props(self, yaml_content: str) -> str:
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        if not isinstance(data, dict):
            raise ValueError("YAML input must be an object (dict) to convert to .properties format.")

        return self.dict_to_props(data)

def run_props_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for props-lab."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Props Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-props")
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

    manager = PropsLabManager()

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
    action = getattr(args, "action", "props2json")  # default direction

    try:
        if action == "props2json":
            result = manager.props2json(input_text)
        elif action == "json2props":
            result = manager.json2props(input_text)
        elif action == "props2yaml":
            result = manager.props2yaml(input_text)
        elif action == "yaml2props":
            result = manager.yaml2props(input_text)
        else:
             print(f"Error: Unknown action '{action}'", file=sys.stderr)
             return False

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
