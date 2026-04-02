import csv
import io
import json
import sys
import yaml  # type: ignore
from pathlib import Path
from typing import Any, Dict, List, Union


class Yaml2CsvManager:
    """Manages the conversion of YAML data to CSV format."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flattens a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def convert(self, yaml_data: Union[str, List[Dict[str, Any]], Dict[str, Any]]) -> str:
        """Converts YAML data to CSV string."""
        if isinstance(yaml_data, str):
            try:
                data = yaml.safe_load(yaml_data)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML string: {e}")
        else:
            data = yaml_data

        if isinstance(data, dict):
            # If it's a single object, make it a list of one object
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("YAML data must be an object or an array of objects.")

        if not data:
            return ""

        # Flatten all objects in the list
        flattened_data = [self._flatten_dict(item) if isinstance(item, dict) else {"value": item} for item in data]

        # Collect all unique keys to form the header
        keys = set()
        for item in flattened_data:
            keys.update(item.keys())

        # Sort keys to ensure consistent column order
        header = sorted(list(keys))

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        for row in flattened_data:
            writer.writerow(row)

        return output.getvalue()


def run_yaml2csv_lab_logic(args):
    """CLI handler for YAML to CSV conversion."""
    manager = Yaml2CsvManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching YAML to CSV Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-yaml2csv")
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

    # CLI mode
    try:
        input_data = None
        if hasattr(args, "text") and args.text:
            input_data = args.text
        elif hasattr(args, "file") and args.file:
            input_path = Path(args.file)
            if not input_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(1)
            input_data = input_path.read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()

        if not input_data:
            print("Error: No input provided. Provide --text, --file or pass YAML via stdin.", file=sys.stderr)
            sys.exit(1)

        csv_output = manager.convert(input_data)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(csv_output, encoding="utf-8")
            print(f"✅ Converted CSV saved to {args.output}")
        else:
            print(csv_output, end="")

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
