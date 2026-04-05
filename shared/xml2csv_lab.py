import argparse
import csv
import sys
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as DefusedET
from pathlib import Path
from io import StringIO
from typing import List, Dict, Any, Optional

class Xml2CsvManager:
    """Manages conversion from XML to CSV format."""

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, str]:
        """Flattens a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # For lists, we just serialize them to strings or ignore deeply nested lists for CSV
                # For simple CSV, stringifying is safest
                items.append((new_key, str(v)))
            else:
                items.append((new_key, str(v) if v is not None else ""))
        return dict(items)

    def _element_to_dict(self, element: ET.Element) -> Any:
        """Converts an XML element to a dictionary, handling attributes and children."""
        result = {}

        # Attributes
        if element.attrib:
            for k, v in element.attrib.items():
                result[f"@{k}"] = v

        # Children
        children = list(element)
        if children:
            for child in children:
                child_data = self._element_to_dict(child)
                tag = child.tag

                if tag in result:
                    if isinstance(result[tag], list):
                        result[tag].append(child_data)
                    else:
                        result[tag] = [result[tag], child_data]
                else:
                    result[tag] = child_data
        elif element.text and element.text.strip():
            # If it has text but no children, the text is the value.
            # If it also has attributes, we put the text under '#text'.
            if result:
                result["#text"] = element.text.strip()
            else:
                return element.text.strip()
        else:
            if not result:
                return None

        return result

    def convert(self, xml_content: str, delimiter: str = ',') -> str:
        """Converts XML string to CSV string."""
        try:
            root = DefusedET.fromstring(xml_content.strip())
        except Exception as e:
            raise ValueError(f"Failed to parse XML: {e}")

        # Convert to dictionary first
        dict_data = self._element_to_dict(root)

        # If the root only has one key, and its value is a list, that's our list of rows
        rows_data = []
        if isinstance(dict_data, dict):
            # check if it's a wrapper for a list of items
            for key, value in dict_data.items():
                if isinstance(value, list):
                    rows_data = value
                    break

            # if no list found, maybe it's just a single record
            if not rows_data:
                rows_data = [dict_data]
        elif isinstance(dict_data, list):
            rows_data = dict_data
        else:
            rows_data = [{"value": dict_data}]

        if not rows_data:
            return ""

        # Flatten each row
        flat_rows = [self._flatten_dict(r) if isinstance(r, dict) else {"value": str(r)} for r in rows_data]

        # Collect all headers
        headers = []
        for r in flat_rows:
            for k in r.keys():
                if k not in headers:
                    headers.append(k)

        # Write to CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers, delimiter=delimiter, lineterminator='\n')
        writer.writeheader()
        writer.writerows(flat_rows)

        return output.getvalue().strip()

    def process_file(self, filepath: Path, output_path: Optional[Path] = None, delimiter: str = ',') -> bool:
        """Processes an XML file and optionally saves to output file."""
        if not filepath.exists():
            print(f"Error: File '{filepath}' not found.", file=sys.stderr)
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        except Exception as e:
            print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
            return False

        try:
            csv_data = self.convert(xml_content, delimiter)
        except Exception as e:
            print(f"Error converting XML: {e}", file=sys.stderr)
            return False

        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(csv_data + '\n')
                print(f"✅ Successfully converted {filepath.name} to {output_path.name}")
                return True
            except Exception as e:
                print(f"Error writing to '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(csv_data)
            return True


def run_xml2csv_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for xml2csv lab."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching XML to CSV Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-xml2csv")
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

    manager = Xml2CsvManager()

    if getattr(args, "file", None):
        filepath = Path(args.file)
        output_path = Path(args.output) if getattr(args, "output", None) else None
        delimiter = getattr(args, "delimiter", ",")
        return manager.process_file(filepath, output_path, delimiter=delimiter)

    if getattr(args, "text", None):
        delimiter = getattr(args, "delimiter", ",")
        try:
            result = manager.convert(args.text, delimiter=delimiter)
            print(result)
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False

    print("Error: Either --file or --text must be provided.", file=sys.stderr)
    return False
