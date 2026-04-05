import csv
import io
import json
import sys
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as DefusedET
from pathlib import Path
from typing import Any, Dict, List, Union

class Xml2CsvManager:
    """Manages conversion between XML and CSV formats."""

    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir

    def _element_to_dict(self, element: ET.Element) -> Any:
        result: Dict[str, Any] = {}

        # Attributes
        if element.attrib:
            result["@attributes"] = element.attrib

        # Text content
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()

        # Children
        for child in element:
            child_data = self._element_to_dict(child)
            tag = child.tag

            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(child_data)
                else:
                    result[tag] = [result[tag], child_data]
            else:
                result[tag] = child_data

        # If element has no attributes and no children, return just the text
        if not element.attrib and len(element) == 0:
            return element.text or ""

        return result

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flattens a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)

    def convert(self, xml_string: str) -> str:
        """Parses an XML string and returns a CSV string."""
        if not xml_string.strip():
            return ""

        try:
            root = DefusedET.fromstring(xml_string)
        except DefusedET.ParseError as e:
            raise ValueError(f"XML Parse Error: {e}")

        data = self._element_to_dict(root)

        # We need a list of dictionaries to convert to CSV
        if isinstance(data, dict):
            # Check if it has child elements that can be treated as rows
            # A common XML structure is <root><item>...</item><item>...</item></root>
            # where data is like {'item': [dict, dict, ...]}

            # Find the first key whose value is a list
            list_key = None
            for k, v in data.items():
                if isinstance(v, list):
                    list_key = k
                    break

            if list_key:
                rows_data = data[list_key]
            else:
                rows_data = [data]
        elif isinstance(data, list):
            rows_data = data
        else:
            rows_data = [{"value": data}]

        # Flatten all objects in the list
        flattened_data = [self._flatten_dict(item) if isinstance(item, dict) else {"value": item} for item in rows_data]

        # Collect all unique keys to form the header
        keys = set()
        for item in flattened_data:
            keys.update(item.keys())

        # Sort keys to ensure consistent column order
        header = sorted(list(keys))

        if not header:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=header)
        writer.writeheader()
        for row in flattened_data:
            writer.writerow(row)

        return output.getvalue()

def run_xml2csv_lab_logic(args):
    """CLI handler for XML to CSV conversion."""
    manager = Xml2CsvManager(getattr(args, 'project_dir', None))

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching XML to CSV Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-xml2csv")
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

    # CLI mode
    try:
        input_data = None
        if hasattr(args, "text") and args.text:
            input_data = args.text
        elif hasattr(args, "file") and args.file:
            input_path = Path(args.file)
            if not input_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(1)
            input_data = input_path.read_text(encoding="utf-8")
        elif not sys.stdin.isatty():
            input_data = sys.stdin.read().strip()

        if not input_data:
            print("Error: No input provided. Provide --text, --file or pass XML via stdin.", file=sys.stderr)
            sys.exit(1)

        csv_output = manager.convert(input_data)

        if hasattr(args, "output") and args.output:
            output_path = Path(args.output)
            output_path.write_text(csv_output, encoding="utf-8")
            print(f"✅ Converted CSV saved to {args.output}")
        else:
            print(csv_output, end="")

    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        sys.exit(1)
