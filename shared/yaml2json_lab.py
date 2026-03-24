import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class Yaml2JsonManager:
    """Manages conversion from YAML to JSON format."""

    def convert(self, yaml_content: str) -> Dict[str, Any]:
        """Converts YAML string to a JSON object/list."""
        try:
            # safe_load securely parses the YAML
            data = yaml.safe_load(yaml_content)
            # return an empty object if YAML is empty
            if data is None:
                return {}
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML: {e}")

    def process_file(self, filepath: Path, output_path: Optional[Path] = None) -> bool:
        """Processes a YAML file and optionally saves to output JSON file."""
        if not filepath.exists():
            print(f"Error: File '{filepath}' not found.", file=sys.stderr)
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
            return False

        try:
            json_data = self.convert(yaml_content)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return False

        json_str = json.dumps(json_data, indent=2)

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(json_str)
            return True


def run_yaml2json_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for yaml2json lab."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching YAML to JSON Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-yaml2json")
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

    manager = Yaml2JsonManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        return manager.process_file(filepath, output_path)

    if getattr(args, "text", None):
        try:
            result = manager.convert(args.text)
            print(json.dumps(result, indent=2))
            return True
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return False

    print("Error: Either --file or --text must be provided.", file=sys.stderr)
    return False
