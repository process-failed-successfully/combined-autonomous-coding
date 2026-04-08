import argparse
import csv
import sys
import xml.etree.ElementTree as ET  # nosec
import defusedxml.minidom as minidom
from pathlib import Path
from io import StringIO
from typing import Optional


class Csv2XmlManager:
    """Manages conversion from CSV to XML format."""

    def convert(self, csv_content: str, delimiter: str = ',', root_element: str = 'root', row_element: str = 'item') -> str:
        """Converts CSV string to an XML string."""
        f = StringIO(csv_content.strip())
        reader = csv.DictReader(f, delimiter=delimiter)

        if not reader.fieldnames:
            return ""

        root = ET.Element(root_element)
        for row in reader:
            item = ET.SubElement(root, row_element)
            for key, value in row.items():
                if key is None:
                    continue  # skip columns without headers

                # Sanitize XML tag name
                tag_name = str(key).strip().replace(' ', '_').replace('/', '_')
                # ensure tag name starts with a letter or underscore
                if tag_name and not (tag_name[0].isalpha() or tag_name[0] == '_'):
                    tag_name = '_' + tag_name

                # if still empty
                if not tag_name:
                    tag_name = 'column'

                child = ET.SubElement(item, tag_name)
                child.text = str(value) if value is not None else ""

        xml_str = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(xml_str)
        return reparsed.toprettyxml(indent="  ")

    def process_file(self, filepath: Path, output_path: Optional[Path] = None, delimiter: str = ',', root_element: str = 'root', row_element: str = 'item') -> bool:
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

        try:
            xml_str = self.convert(csv_content, delimiter, root_element, row_element)
        except Exception as e:
            print(f"Failed to parse CSV or generate XML: {e}", file=sys.stderr)
            raise ValueError(f"Failed to parse CSV or generate XML: {e}")

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(xml_str)
            return True


def run_csv2xml_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for csv2xml lab."""
    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching CSV to XML Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-csv2xml")
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

    manager = Csv2XmlManager()

    delimiter = getattr(args, "delimiter", ",")
    root_el = getattr(args, "root", "root")
    row_el = getattr(args, "row", "item")

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        return manager.process_file(filepath, output_path, delimiter=delimiter, root_element=root_el, row_element=row_el)

    text_input = getattr(args, "text", None)
    if text_input is None and not sys.stdin.isatty():
        text_input = sys.stdin.read().strip()

    if text_input is not None:
        try:
            result = manager.convert(text_input, delimiter=delimiter, root_element=root_el, row_element=row_el)

            output_path = Path(args.output) if getattr(args, "output", None) else None
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"✅ Successfully converted to {output_path.name}")
            else:
                print(result)
            return True
        except Exception as e:
            print(f"Error converting CSV to XML: {e}", file=sys.stderr)
            return False

    print("Error: No input provided.", file=sys.stderr)
    return False
