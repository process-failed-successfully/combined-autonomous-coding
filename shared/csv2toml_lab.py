import argparse
import csv
import sys
from pathlib import Path
from io import StringIO
from typing import Optional

import tomlkit


class Csv2TomlManager:
    """Manages conversion from CSV to TOML format."""

    def convert(self, csv_content: str, delimiter: str = ',') -> str:
        """Converts CSV string to a TOML string."""
        f = StringIO(csv_content.strip())
        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            return ""

        doc = tomlkit.document()
        items = tomlkit.aot()

        for row in reader:
            table = tomlkit.table()
            for k, v in row.items():
                if k is None:
                    continue
                table.add(str(k), v)
            items.append(table)

        if items:
            doc.add("items", items)

        return tomlkit.dumps(doc)

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

        toml_str = self.convert(csv_content, delimiter)

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(toml_str)
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(toml_str)
            return True


def run_csv2toml_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for csv2toml lab."""
    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching CSV to TOML Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-csv2toml")
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

    manager = Csv2TomlManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        delimiter = getattr(args, "delimiter", ",")
        return manager.process_file(filepath, output_path, delimiter=delimiter)

    if getattr(args, "text", None):
        delimiter = getattr(args, "delimiter", ",")
        result = manager.convert(args.text, delimiter=delimiter)
        print(result)
        return True

    print("Error: Either --file or --text must be provided.", file=sys.stderr)
    return False
