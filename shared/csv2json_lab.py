import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class Csv2JsonManager:
    """Manages the conversion of CSV data to JSON format."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir

    def convert(self, csv_data: str, delimiter: str = ",") -> str:
        """Converts CSV string to a JSON string array of objects."""
        if not csv_data or not csv_data.strip():
            return "[]"

        # Read the CSV data
        f = io.StringIO(csv_data)
        reader = csv.DictReader(f, delimiter=delimiter)

        # If the file is just headers or empty but not empty string,
        # DictReader might not yield any rows.

        rows = []
        for row in reader:
            # Clean up the parsed row to remove any None keys that might occur if
            # there are more columns than headers, or None values if fewer.
            # Convert values appropriately (e.g. keep them as strings for simplicity
            # as it's standard CSV behavior, or attempt to parse numbers if strictly needed.
            # We will stick to string parsing as standard Csv2Json does.)
            clean_row = {k: (v if v is not None else "") for k, v in row.items() if k is not None}
            rows.append(clean_row)

        return json.dumps(rows, indent=2)


def run_csv2json_lab_logic(args):
    """CLI handler for CSV to JSON conversion."""
    manager = Csv2JsonManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching CSV to JSON Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-csv2json")
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
        elif hasattr(args, "text") and args.text:
            input_data = args.text
        elif not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()
        else:
            print("Error: No input provided. Provide --file, --text, or pass CSV via stdin.", file=sys.stderr)
            sys.exit(1)

        delimiter = getattr(args, "delimiter", ",")
        json_output = manager.convert(input_data, delimiter=delimiter)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(json_output, encoding="utf-8")
            print(f"✅ Converted JSON saved to {args.output}")
        else:
            print(json_output)

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
