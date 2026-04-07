"""
Markdown to CSV Lab
===================

Utilities for converting Markdown tables into CSV strings or files.
"""

import csv
import io
import sys
import re
from pathlib import Path

class Md2CsvManager:
    """Manages conversion between Markdown tables and CSV format."""

    def convert_to_csv(self, md_data: str, delimiter: str = ',') -> str:
        """
        Converts a Markdown table string to a CSV string.
        """
        if not md_data or not md_data.strip():
            return ""

        lines = md_data.strip().split('\n')
        rows = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if it's a markdown table row (starts and ends with | or contains |)
            if not '|' in line:
                continue

            # Remove leading and trailing pipes if they exist
            if line.startswith('|'):
                line = line[1:]
            if line.endswith('|'):
                line = line[:-1]

            # Split by pipe and strip whitespace from cells
            cells = [cell.strip() for cell in line.split('|')]
            rows.append(cells)

        if not rows:
            return ""

        # Remove the separator row if it exists (usually the second row, like |---|---|)
        if len(rows) > 1:
            is_separator = True
            for cell in rows[1]:
                # Check if cell consists only of -, :, and whitespace
                if not re.match(r'^[\s\-:]+$', cell):
                    is_separator = False
                    break

            if is_separator:
                rows.pop(1)

        # Write to CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        writer.writerows(rows)

        return output.getvalue()

def run_md2csv_lab_logic(args) -> bool:
    """CLI handler for Markdown to CSV Lab."""

    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Markdown to CSV Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-md2csv")

        # Support asyncio loop checking
        if hasattr(app, 'run_async'):
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
        else:
            app.run()
            sys.exit(0)
        return True

    manager = Md2CsvManager()
    md_data = ""

    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                md_data = f.read()
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        md_data = args.text
    else:
        # Check if stdin has data
        if not sys.stdin.isatty():
            md_data = sys.stdin.read()
        else:
            print("Error: No input provided. Use --file, --text, or stdin.", file=sys.stderr)
            return False

    delimiter = getattr(args, "delimiter", ",")

    try:
        csv_output = manager.convert_to_csv(md_data, delimiter=delimiter)
    except ValueError as e:
        print(f"Error converting Markdown to CSV: {e}", file=sys.stderr)
        return False

    output_file = getattr(args, "output", None)
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(csv_output)
            print(f"✅ Successfully wrote CSV data to '{output_file}'.")
        except Exception as e:
            print(f"Error writing to file '{output_file}': {e}", file=sys.stderr)
            return False
    else:
        print(csv_output)

    return True
