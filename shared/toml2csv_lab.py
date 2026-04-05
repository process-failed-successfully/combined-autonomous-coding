import csv
import io
import json
import sys
import tomlkit
from pathlib import Path
from typing import Any, Dict, List, Union


class Toml2CsvManager:
    """Manages the conversion of TOML data to CSV format."""

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
                # We convert lists to a JSON string representation
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def convert(self, toml_data: str, delimiter: str = ',') -> str:
        """Converts TOML data to CSV string."""
        if not toml_data.strip():
            return ""

        try:
            parsed_toml = tomlkit.parse(toml_data)
        except Exception as e:
            raise ValueError(f"Invalid TOML string: {e}")

        # Try to find a list of objects (array of tables) to use as rows
        # If the root has a key containing a list of dicts, we use that list
        # E.g. [[items]] in TOML translates to {'items': [dict, dict]}
        rows_data = None
        for k, v in parsed_toml.items():
            if isinstance(v, list) and all(isinstance(item, dict) for item in v):
                rows_data = v
                break

        # If no array of tables is found, treat the root document as a single row
        if rows_data is None:
            rows_data = [parsed_toml]

        # Flatten all objects in the list
        flattened_data = [self._flatten_dict(item) if isinstance(item, dict) else {"value": item} for item in rows_data]

        # Collect all unique keys to form the header
        keys = set()
        for item in flattened_data:
            keys.update(item.keys())

        # Sort keys to ensure consistent column order
        header = sorted(list(keys))

        if not header:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header, delimiter=delimiter)
        writer.writeheader()
        for row in flattened_data:
            writer.writerow(row)

        return output.getvalue()


def run_toml2csv_lab_logic(args):
    """CLI handler for TOML to CSV conversion."""
    manager = Toml2CsvManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching TOML to CSV Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-toml2csv")
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
        else:
            print("Error: No input provided. Provide --file, --text or pass TOML via stdin.", file=sys.stderr)
            sys.exit(1)

        delimiter = getattr(args, 'delimiter', ',')
        csv_output = manager.convert(input_data, delimiter=delimiter)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(csv_output, encoding="utf-8")
            print(f"✅ Converted CSV saved to {args.output}")
        else:
            print(csv_output, end="")

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
