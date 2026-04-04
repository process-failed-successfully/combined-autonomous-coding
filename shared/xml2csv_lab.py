import sys
import argparse
import csv
import io
from defusedxml import ElementTree as ET
from pathlib import Path


class Xml2CsvManager:
    """Manages conversion from XML to CSV."""

    def convert_xml_to_csv(self, xml_content: str) -> str:
        """Converts an XML string to a CSV string."""
        if not xml_content or not xml_content.strip():
            return ""

        try:
            root = ET.fromstring(xml_content.strip())
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}")

        # Try to find a list of records.
        # We assume the root contains multiple identical children (records),
        # or the root itself is the single record if it has children.

        # Let's find all children of root
        children = list(root)

        if not children:
            # Empty root or just text
            return ""

        # Check if children have children (list of records)
        first_child = children[0]
        has_grandchildren = len(list(first_child)) > 0

        records = []
        if has_grandchildren:
            # Assume each child of root is a record
            for child in children:
                record = {}
                for subchild in child:
                    record[subchild.tag] = subchild.text if subchild.text else ""
                records.append(record)
        else:
            # Assume root is the single record
            record = {}
            for child in root:
                record[child.tag] = child.text if child.text else ""
            records.append(record)

        # If there are no records, this block would be hit, but it's handled above implicitly.
        # Leaving for safety in case of logical changes
        if not records: # pragma: no cover
            return ""

        # Collect all headers
        headers = []
        for record in records:
            for key in record.keys():
                if key not in headers:
                    headers.append(key)

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

        return output.getvalue().strip()


def run_xml2csv_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for Xml2Csv Lab."""
    manager = Xml2CsvManager()

    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching Xml2Csv Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, "project_dir", Path(".")), start_tab="tab-xml2csv")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running(): # pragma: no cover
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        return True

    input_content = ""
    if getattr(args, "file", None):
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            return False
        try:
            input_content = path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        input_content = args.text
    else:
        # Check if stdin has data
        if not sys.stdin.isatty():
            input_content = sys.stdin.read()
        else:
            print("Error: No input provided. Use --file, --text, or pipe input.", file=sys.stderr)
            return False

    try:
        csv_output = manager.convert_xml_to_csv(input_content)

        if getattr(args, "output", None):
            out_path = Path(args.output)
            out_path.write_text(csv_output, encoding="utf-8")
            print(f"Successfully wrote to {args.output}")
        else:
            print(csv_output)
        return True
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False
