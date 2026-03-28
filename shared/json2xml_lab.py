import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class Json2XmlManager:
    """
    Manages JSON to XML conversion.
    """

    def _dict_to_element(self, parent: ET.Element, data: Any) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "@attributes" and isinstance(value, dict):
                    for attr_k, attr_v in value.items():
                        parent.set(attr_k, str(attr_v))
                elif key == "#text":
                    parent.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(parent, key)
                            self._dict_to_element(child, item)
                    else:
                        child = ET.SubElement(parent, key)
                        self._dict_to_element(child, value)
        elif isinstance(data, list):
            # This case implies a list of items where the tag name is unknown.
            # Usually handled in the dict iteration above. If root is a list,
            # we must wrap it. This is handled in `convert_string` logic.
            for item in data:
                child = ET.SubElement(parent, "item")
                self._dict_to_element(child, item)
        else:
            if data is not None:
                parent.text = str(data)

    def convert_string(self, json_string: str) -> str:
        """Parses a JSON string and returns an XML string."""
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON Parse Error: {e}")

        if not isinstance(data, dict):
            # JSON root is not an object, wrap it
            root = ET.Element("root")
            self._dict_to_element(root, data)
        elif len(data) == 1:
            # Single root key
            root_key = list(data.keys())[0]
            root = ET.Element(root_key)
            self._dict_to_element(root, data[root_key])
        else:
            # Multiple root keys, need a wrapper
            root = ET.Element("root")
            self._dict_to_element(root, data)

        try:
            # Pretty print (Python 3.9+)
            ET.indent(root, space="  ", level=0)
        except AttributeError:
            pass  # fallback if python version < 3.9

        xml_str = ET.tostring(root, encoding="unicode", xml_declaration=False)
        return xml_str

    def convert_file(self, filepath: Path) -> str:
        """Parses a JSON file and returns an XML string."""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                json_string = f.read()
            return self.convert_string(json_string)
        except Exception as e:
            raise ValueError(f"Error reading or parsing {filepath}: {e}")


def run_json2xml_lab_logic(args):
    """CLI Entry point for JSON to XML conversion."""
    manager = Json2XmlManager()

    try:
        if getattr(args, "file", None):
            filepath = Path(args.file)
            xml_output = manager.convert_file(filepath)
        elif getattr(args, "text", None):
            xml_output = manager.convert_string(args.text)
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
            xml_output = manager.convert_string(content)
        else:
            print("Error: Input file, text, or stdin required.", file=sys.stderr)
            sys.exit(1)

        if getattr(args, "output", None):
            output_path = Path(args.output)
            output_path.write_text(xml_output, encoding="utf-8")
            print(f"✅ Saved XML to {output_path}")
        else:
            print(xml_output)

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
