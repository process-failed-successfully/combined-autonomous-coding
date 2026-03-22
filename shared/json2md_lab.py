import argparse
import json
import sys
from pathlib import Path

class Json2MdManager:
    def convert(self, data) -> str:
        """Converts parsed JSON data (dict or list) to a Markdown table."""
        if not data:
            return ""

        if isinstance(data, dict):
            # Single object: 2 columns (Key, Value)
            headers = ["Key", "Value"]
            rows = [[str(k), self._format_value(v)] for k, v in data.items()]
            return self._build_table(headers, rows)

        elif isinstance(data, list):
            if not data:
                return ""

            # List of items
            first_item = data[0]
            if isinstance(first_item, dict):
                # Extract all unique keys across all dictionaries to form headers
                headers = []
                for item in data:
                    if isinstance(item, dict):
                        for k in item.keys():
                            if str(k) not in headers:
                                headers.append(str(k))

                rows = []
                for item in data:
                    if isinstance(item, dict):
                        row = [self._format_value(item.get(h, "")) for h in headers]
                        rows.append(row)
                    else:
                        # Fallback for non-dict items in a mixed list
                        row = [self._format_value(item)] + [""] * (len(headers) - 1)
                        rows.append(row)

                return self._build_table(headers, rows)
            else:
                # List of primitives
                headers = ["Index", "Value"]
                rows = [[str(i), self._format_value(v)] for i, v in enumerate(data)]
                return self._build_table(headers, rows)

        else:
            # Primitive value
            return str(data)

    def _format_value(self, val) -> str:
        """Formats a value for inclusion in a Markdown table cell."""
        if val is None:
            return ""
        if isinstance(val, (dict, list)):
             # Compact JSON string for nested objects
             s = json.dumps(val, separators=(',', ':'))
             # Escape pipe characters so it doesn't break the Markdown table
             return s.replace("|", "\\|").replace("\n", " ")

        s = str(val)
        return s.replace("|", "\\|").replace("\n", "<br>")

    def _build_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """Builds a Markdown table string from headers and rows."""
        if not headers:
            return ""

        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"

        table_lines = [header_row, separator_row]
        for row in rows:
            table_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(table_lines)


def run_json2md_lab_logic(args: argparse.Namespace) -> bool:
    manager = Json2MdManager()

    data = None
    if getattr(args, "file", None):
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from file: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False

    elif getattr(args, "text", None):
        try:
            data = json.loads(args.text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON string: {e}", file=sys.stderr)
            return False

    else:
        print("Error: Must provide either --file, --text, or --tui", file=sys.stderr)
        return False

    try:
        md_table = manager.convert(data)

        if getattr(args, "output", None):
            out_path = Path(args.output)
            out_path.write_text(md_table, encoding="utf-8")
            print(f"Markdown table saved to {out_path}")
        else:
            print(md_table)

        return True
    except Exception as e:
        print(f"Error converting JSON to Markdown: {e}", file=sys.stderr)
        return False
