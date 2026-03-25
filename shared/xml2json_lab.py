import argparse
import json
import sys
from typing import Any, Optional
from pathlib import Path
import defusedxml.ElementTree as ET  # nosec B405
import xml.etree.ElementTree as pyET  # nosec B405


class Xml2JsonManager:
    def convert(self, xml_string: Optional[str]) -> str:
        """Converts an XML string to a JSON string."""
        if not xml_string or not xml_string.strip():
            return "{}"

        try:
            root = ET.fromstring(xml_string)
            data = {root.tag: self._element_to_dict(root)}
            return json.dumps(data, indent=2)
        except pyET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}")

    def _element_to_dict(self, element: pyET.Element):
        """Recursively converts an ElementTree element to a dictionary."""
        result = {}

        # Handle attributes
        if element.attrib:
            for k, v in element.attrib.items():
                result[f"@{k}"] = v

        # Handle text content
        text = element.text.strip() if element.text else ""

        # Handle children
        children = list(element)
        if children:
            child_dict: dict[str, Any] = {}
            for child in children:
                child_result = self._element_to_dict(child)
                if child.tag in child_dict:
                    if isinstance(child_dict[child.tag], list):
                        child_dict[child.tag].append(child_result)
                    else:
                        child_dict[child.tag] = [child_dict[child.tag], child_result]
                else:
                    child_dict[child.tag] = child_result
            result.update(child_dict)
        elif text:
            # If it only has text and no attributes, return just the text
            if not result:
                return text
            else:
                result["#text"] = text

        return result


def run_xml2json_lab_logic(args: argparse.Namespace) -> bool:
    manager = Xml2JsonManager()

    data_xml = None
    if getattr(args, "file", None):
        path = Path(args.file)
        if not path.is_file():
            print(f"Error: File '{args.file}' not found.", file=sys.stderr)
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data_xml = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False

    elif getattr(args, "text", None):
        data_xml = args.text

    else:
        print("Error: Must provide either --file, --text, or --tui", file=sys.stderr)
        return False

    try:
        json_output = manager.convert(data_xml)

        if getattr(args, "output", None):
            out_path = Path(args.output)
            out_path.write_text(json_output, encoding="utf-8")
            print(f"JSON saved to {out_path}")
        else:
            print(json_output)

        return True
    except ValueError as e:
        print(f"Error converting XML to JSON: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False
