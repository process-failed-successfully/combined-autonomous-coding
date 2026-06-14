import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union


class Csv2JsonlManager:
    """Manages the conversion of CSV data to JSON Lines format."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def convert(self, csv_data: str, delimiter: str = ',') -> str:
        """Converts CSV data to JSON Lines string."""
        if not csv_data.strip():
            return ""

        input_io = io.StringIO(csv_data)
        reader = csv.DictReader(input_io, delimiter=delimiter)

        jsonl_lines = []
        for row in reader:
            # We filter out None values or similar empty cases if desired,
            # but usually preserving keys is better. We will preserve them.
            jsonl_lines.append(json.dumps(row, separators=(',', ':')))

        return "\n".join(jsonl_lines)


def run_csv2jsonl_lab_logic(args):
    """CLI handler for CSV to JSON Lines conversion."""
    manager = Csv2JsonlManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching CSV to JSON Lines Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-csv2jsonl")
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
            print("Error: No input provided. Provide --text, --file or pass CSV via stdin.", file=sys.stderr)
            sys.exit(1)

        delimiter = getattr(args, "delimiter", ",")
        jsonl_output = manager.convert(input_data, delimiter=delimiter)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(jsonl_output, encoding="utf-8")
            print(f"✅ Converted JSON Lines saved to {args.output}")
        else:
            print(jsonl_output)

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
