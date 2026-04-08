"""
CSV to XML Lab
==============

Provides functionality to convert CSV data into XML.
"""

import csv
import sys
import io
import argparse
import xml.etree.ElementTree as ET  # nosec B405
from xml.dom import minidom
from typing import Optional, List, Dict, Any

class Csv2XmlManager:
    """Manages CSV to XML conversion."""

    def convert(self, csv_data: str, delimiter: str = ',', root_name: str = 'root', item_name: str = 'item') -> str:
        """Converts CSV string to an XML string."""
        if not csv_data.strip():
            return ""

        f = io.StringIO(csv_data)
        reader = csv.reader(f, delimiter=delimiter)

        rows = list(reader)
        if not rows:
            return ""

        headers = rows.pop(0)

        # Clean headers to be valid XML tags
        clean_headers = []
        for header in headers:
            clean = "".join(c for c in header if c.isalnum() or c in ['_', '-'])
            if not clean or clean[0].isdigit() or clean[0] == '-':
                clean = "col_" + clean
            clean_headers.append(clean)

        root = ET.Element(root_name)

        for row in rows:
            item = ET.SubElement(root, item_name)
            for i, val in enumerate(row):
                if i < len(clean_headers):
                    col_name = clean_headers[i]
                else:
                    col_name = f"col_{i}"

                child = ET.SubElement(item, col_name)
                child.text = val

        # Format with minidom for pretty printing
        xmlstr = ET.tostring(root, encoding='utf-8', method='xml')
        dom = minidom.parseString(xmlstr)  # nosec B318
        pretty_xml = dom.toprettyxml(indent="  ")

        # Remove the XML declaration if it's there
        lines = pretty_xml.split('\n')
        if lines and lines[0].startswith('<?xml'):
            lines = lines[1:]

        # Also minidom adds lots of blank lines sometimes
        return '\n'.join([line for line in lines if line.strip()]).strip()


def run_csv2xml_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for csv2xml-lab."""
    manager = Csv2XmlManager()

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
    root_name = getattr(args, "root", "root")
    item_name = getattr(args, "item", "item")

    try:
        xml_output = manager.convert(
            csv_data,
            delimiter=delimiter,
            root_name=root_name,
            item_name=item_name
        )

        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(xml_output)
            print(f"✅ XML saved to {args.output}")
        else:
            print(xml_output)

        return True
    except Exception as e:
        print(f"❌ Error during conversion: {e}", file=sys.stderr)
        return False
