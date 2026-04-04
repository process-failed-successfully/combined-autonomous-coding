"""
CSV to HTML Lab
===============

Provides functionality to convert CSV data into HTML tables.
"""

import csv
import sys
import io
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any

class Csv2HtmlManager:
    """Manages CSV to HTML conversion."""

    def convert(self, csv_data: str, delimiter: str = ',', has_header: bool = True, table_class: str = "", table_id: str = "") -> str:
        """Converts CSV string to an HTML table string."""
        if not csv_data.strip():
            return ""

        f = io.StringIO(csv_data)
        reader = csv.reader(f, delimiter=delimiter)

        rows = list(reader)
        if not rows:
            return ""

        html = []

        table_attrs = []
        if table_id:
            table_attrs.append(f'id="{table_id}"')
        if table_class:
            table_attrs.append(f'class="{table_class}"')

        attr_str = " " + " ".join(table_attrs) if table_attrs else ""
        html.append(f"<table{attr_str}>")

        if has_header:
            headers = rows.pop(0)
            html.append("  <thead>")
            html.append("    <tr>")
            for header in headers:
                html.append(f"      <th>{self._escape_html(header)}</th>")
            html.append("    </tr>")
            html.append("  </thead>")

        html.append("  <tbody>")
        for row in rows:
            html.append("    <tr>")
            for cell in row:
                html.append(f"      <td>{self._escape_html(cell)}</td>")
            html.append("    </tr>")
        html.append("  </tbody>")
        html.append("</table>")

        return "\n".join(html)

    def _escape_html(self, text: str) -> str:
        """Basic HTML escaping."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;")

def run_csv2html_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for csv2html-lab."""
    manager = Csv2HtmlManager()

    csv_data = ""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                csv_data = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    elif getattr(args, "text", None):
        csv_data = args.text
    else:
        if not sys.stdin.isatty():
            csv_data = sys.stdin.read()
        else:
            print("Error: Input required via --file, --text, or stdin.", file=sys.stderr)
            sys.exit(1)

    delimiter = getattr(args, "delimiter", ",")
    has_header = not getattr(args, "no_header", False)
    table_class = getattr(args, "table_class", "")
    table_id = getattr(args, "table_id", "")

    try:
        html_output = manager.convert(
            csv_data,
            delimiter=delimiter,
            has_header=has_header,
            table_class=table_class,
            table_id=table_id
        )

        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html_output)
            print(f"✅ HTML saved to {args.output}")
        else:
            print(html_output)

        return True
    except Exception as e:
        print(f"❌ Error during conversion: {e}", file=sys.stderr)
        return False
