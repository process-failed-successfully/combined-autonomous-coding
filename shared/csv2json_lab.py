import argparse
import csv
import json
import sys
from pathlib import Path
from io import StringIO
from typing import List, Dict, Any, Optional

class Csv2JsonManager:
    """Manages conversion from CSV to JSON format."""

    def convert(self, csv_content: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Converts CSV string to a list of JSON objects."""
        f = StringIO(csv_content.strip())
        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            return []

        result = []
        for row in reader:
            result.append(row)

        return result

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

        json_data = self.convert(csv_content, delimiter)
        json_str = json.dumps(json_data, indent=2)

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(json_str)
            return True


def run_csv2json_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for csv2json lab."""
    manager = Csv2JsonManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        delimiter = getattr(args, "delimiter", ",")
        return manager.process_file(filepath, output_path, delimiter=delimiter)

    if getattr(args, "text", None):
        delimiter = getattr(args, "delimiter", ",")
        result = manager.convert(args.text, delimiter=delimiter)
        print(json.dumps(result, indent=2))
        return True

    print("Error: Either --file or --text must be provided.", file=sys.stderr)
    return False
