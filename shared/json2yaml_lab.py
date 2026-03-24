import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class Json2YamlManager:
    """Manages conversion from JSON to YAML format."""

    def convert(self, json_content: str) -> str:
        """Converts JSON string to a YAML string."""
        try:
            data = json.loads(json_content)
            # return an empty object if JSON is empty string (though json.loads fails on empty)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON: {e}")

        try:
            # dump to string
            yaml_str = yaml.dump(data, sort_keys=False, default_flow_style=False)
            return yaml_str
        except yaml.YAMLError as e:
            raise ValueError(f"Error writing YAML: {e}")

    def process_file(self, filepath: Path, output_path: Optional[Path] = None) -> bool:
        """Processes a JSON file and optionally saves to output YAML file."""
        if not filepath.exists():
            print(f"Error: File '{filepath}' not found.", file=sys.stderr)
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_content = f.read()
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
            return False

        try:
            yaml_str = self.convert(json_content)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return False

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(yaml_str)
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(yaml_str)
            return True


def run_json2yaml_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for json2yaml lab."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching JSON to YAML Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2yaml")
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

    manager = Json2YamlManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        return manager.process_file(filepath, output_path)

    if getattr(args, "text", None):
        try:
            result = manager.convert(args.text)
            print(result)
            return True
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return False

    print("Error: Either --file or --text must be provided.", file=sys.stderr)
    return False
