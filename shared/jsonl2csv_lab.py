import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union


class Jsonl2CsvManager:
    """Manages the conversion of JSON Lines data to CSV format."""

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

    def convert(self, jsonl_data: str) -> str:
        """Converts JSON Lines data to CSV string."""
        if not jsonl_data.strip():
            return ""

        data = []
        lines = jsonl_data.strip().split('\n')
        for i, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError(f"Line {i} is valid JSON but not a JSON object.")
                data.append(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {i}: {e}")

        if not data:
            return ""

        flattened_data = [self._flatten_dict(item) for item in data]

        keys = set()
        for item in flattened_data:
            keys.update(item.keys())

        header = sorted(list(keys))

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        for row in flattened_data:
            writer.writerow(row)

        return output.getvalue()


def run_jsonl2csv_lab_logic(args):
    """CLI handler for JSON Lines to CSV conversion."""
    manager = Jsonl2CsvManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching JSON Lines to CSV Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-jsonl2csv")
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
        if hasattr(args, "file") and args.file:
            input_path = Path(args.file)
            if not input_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(1)
            input_data = input_path.read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()
        else:
            print("Error: No input provided. Provide --file or pass JSON Lines via stdin.", file=sys.stderr)
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
