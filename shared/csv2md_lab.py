import argparse
import csv
import sys
from pathlib import Path
from io import StringIO
from typing import Optional


class Csv2MdManager:
    """Manages conversion from CSV to Markdown tables."""

    def convert(self, csv_content: str, delimiter: str = ',') -> str:
        """Converts CSV string to a Markdown table."""
        f = StringIO(csv_content.strip())
        reader = csv.reader(f, delimiter=delimiter)

        try:
            headers = next(reader)
        except StopIteration:
            return ""

        if not headers:
            return ""

        # Build markdown table header
        md_lines = []
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("|" + "|".join(["---"] * len(headers)) + "|")

        for row in reader:
            # Pad row with empty strings if it has fewer columns than headers
            row = row + [""] * (len(headers) - len(row))
            # Truncate row if it has more columns than headers
            row = row[:len(headers)]
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def process_file(self, filepath: Path, output_path: Optional[Path] = None, delimiter: str = ',') -> bool:
        """Processes a CSV file and optionally saves to output file."""
        if not filepath.exists():
            print(f"Error: File '{filepath}' not found.", file=sys.stderr)
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                csv_content = f.read()
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
            return False

        md_str = self.convert(csv_content, delimiter)

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_str)
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(md_str)
            return True


def run_csv2md_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for csv2md lab."""
    manager = Csv2MdManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        delimiter = getattr(args, "delimiter", ",")
        return manager.process_file(filepath, output_path, delimiter=delimiter)

    if getattr(args, "text", None):
        delimiter = getattr(args, "delimiter", ",")
        # Replace literal \n with actual newline if passed from shell
        text = args.text.replace('\\n', '\n')
        result = manager.convert(text, delimiter=delimiter)
        print(result)
        return True

    print("Error: Either --file or --text must be provided.", file=sys.stderr)
    return False
