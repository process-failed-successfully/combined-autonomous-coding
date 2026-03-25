import sys
import json
import defusedxml.ElementTree as ET
import xml.etree.ElementTree as pyET  # nosec B405
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

class Xml2JsonManager:
    """
    Manages XML to JSON conversion.
    """

    def _element_to_dict(self, element: pyET.Element) -> Any:
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

    def convert_string(self, xml_string: str) -> Dict[str, Any]:
        """Parses an XML string and returns a Python dictionary."""
        try:
            root = ET.fromstring(xml_string)
            return {root.tag: self._element_to_dict(root)}
        except pyET.ParseError as e:
            raise ValueError(f"XML Parse Error: {e}")

    def convert_file(self, filepath: Path) -> Dict[str, Any]:
        """Parses an XML file and returns a Python dictionary."""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            return {root.tag: self._element_to_dict(root)}
        except pyET.ParseError as e:
            raise ValueError(f"XML Parse Error in {filepath}: {e}")

def run_xml2json_lab_logic(args):
    """CLI Entry point for XML to JSON conversion."""
    manager = Xml2JsonManager()

    try:
        if getattr(args, "file", None):
            filepath = Path(args.file)
            data = manager.convert_file(filepath)
        elif getattr(args, "text", None):
            data = manager.convert_string(args.text)
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
            data = manager.convert_string(content)
        else:
            print("Error: Input file, text, or stdin required.", file=sys.stderr)
            sys.exit(1)

        json_output = json.dumps(data, indent=2)

        if getattr(args, "output", None):
            output_path = Path(args.output)
            output_path.write_text(json_output, encoding="utf-8")
            print(f"✅ Saved JSON to {output_path}")
        else:
            print(json_output)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
