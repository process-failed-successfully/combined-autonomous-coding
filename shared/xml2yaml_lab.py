import sys
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as DefusedET
import yaml  # type: ignore
from pathlib import Path
from typing import Dict, Any


class Xml2YamlManager:
    """Manages conversion between XML and YAML formats."""

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

    def convert_xml_to_yaml(self, xml_string: str) -> str:
        """Parses an XML string and returns a YAML string."""
        try:
            root = DefusedET.fromstring(xml_string)
            data = {root.tag: self._element_to_dict(root)}
            return yaml.dump(data, sort_keys=False, default_flow_style=False)
        except DefusedET.ParseError as e:
            raise ValueError(f"XML Parse Error: {e}")

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
            for item in data:
                child = ET.SubElement(parent, "item")
                self._dict_to_element(child, item)
        else:
            if data is not None:
                parent.text = str(data)

    def convert_yaml_to_xml(self, yaml_string: str) -> str:
        """Parses a YAML string and returns an XML string."""
        try:
            data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML Parse Error: {e}")

        if not isinstance(data, dict):
            # YAML root is not an object, wrap it
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


def run_xml2yaml_lab_logic(args):
    """CLI handler for Xml2Yaml Lab."""
    manager = Xml2YamlManager()

    # We will read from args.input if it's not None
    # We distinguish between file, text, or stdin.

    action = getattr(args, "action", None)
    if action not in ("xml2yaml", "yaml2xml"):
        print(f"Error: Invalid action '{action}'.", file=sys.stderr)
        return False

    try:
        input_data = getattr(args, "input", None)
        if not input_data:
            if not sys.stdin.isatty():
                input_data = sys.stdin.read()
            else:
                print("Error: Input required.", file=sys.stderr)
                return False

        # Try to treat input_data as file path if short enough,
        # though usually CLI arg parser handles reading files vs strings.
        # But we'll do what yaml2json_lab does.
        if len(input_data) < 1000:
            path = Path(input_data)
            if path.exists() and path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = input_data
        else:
            content = input_data

        if action == "xml2yaml":
            result = manager.convert_xml_to_yaml(content)
        else:
            result = manager.convert_yaml_to_xml(content)

        output = getattr(args, "output", None)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Output written to {output}")
        else:
            print(result)

        return True
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
