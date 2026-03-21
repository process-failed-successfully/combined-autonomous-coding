"""
CSV to Markdown Lab
===================

Utilities for converting CSV strings or files into Markdown tables.
"""

import csv
import io
import sys
from pathlib import Path
from typing import List, Tuple

class Csv2MdManager:
    """Manages conversion between CSV format and Markdown tables."""

    def convert_to_markdown(self, csv_data: str, delimiter: str = ',') -> str:
        """
        Converts a CSV string to a Markdown table string.
        """
        if not csv_data or not csv_data.strip():
            return ""

        f = io.StringIO(csv_data.strip())
        reader = csv.reader(f, delimiter=delimiter)

        try:
            rows = list(reader)
        except csv.Error as e:
            raise ValueError(f"Error parsing CSV: {e}")

        if not rows:
            return ""

        # Normalize rows to have the same number of columns as the header
        header = rows[0]
        num_columns = len(header)
        normalized_rows = []
        for row in rows:
            if len(row) < num_columns:
                row.extend([""] * (num_columns - len(row)))
            elif len(row) > num_columns:
                row = row[:num_columns]
            normalized_rows.append([cell.strip().replace("\n", " ") for cell in row])

        # Find max width for each column
        col_widths = [0] * num_columns
        for row in normalized_rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(cell))

        # Function to format a single row
        def format_row(row: List[str]) -> str:
            padded_cells = [cell.ljust(col_widths[i]) for i, cell in enumerate(row)]
            return "| " + " | ".join(padded_cells) + " |"

        md_lines = []

        # Add header
        md_lines.append(format_row(normalized_rows[0]))

        # Add separator
        separator = "| " + " | ".join("-" * max(3, w) for w in col_widths) + " |"
        md_lines.append(separator)

        # Add data rows
        for row in normalized_rows[1:]:
            md_lines.append(format_row(row))

        return "\n".join(md_lines)

def run_csv2md_lab_logic(args) -> bool:
    """CLI handler for CSV to Markdown Lab."""

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching CSV to Markdown Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-csv2md")

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

    manager = Csv2MdManager()
    csv_data = ""

    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                csv_data = f.read()
        except Exception as e:
            print(f"Error reading file '{args.file}': {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        csv_data = args.text
    else:
        # Check if stdin has data
        if not sys.stdin.isatty():
            csv_data = sys.stdin.read()
        else:
            print("Error: No input provided. Use --file, --text, or stdin.", file=sys.stderr)
            return False

    delimiter = getattr(args, "delimiter", ",")

    try:
        md_output = manager.convert_to_markdown(csv_data, delimiter=delimiter)
    except ValueError as e:
        print(f"Error converting CSV to Markdown: {e}", file=sys.stderr)
        return False

    output_file = getattr(args, "output", None)
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_output)
            print(f"✅ Successfully wrote Markdown table to '{output_file}'.")
        except Exception as e:
            print(f"Error writing to file '{output_file}': {e}", file=sys.stderr)
            return False
    else:
        print(md_output)

    return True
