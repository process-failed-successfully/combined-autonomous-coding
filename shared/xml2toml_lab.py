import sys
import tomlkit
import defusedxml.ElementTree as DefusedET
from pathlib import Path
from typing import Dict, Any


class Xml2TomlManager:
    """Manages conversion between XML and TOML formats."""

    def _element_to_dict(self, element) -> Any:
        result: Dict[str, Any] = {}
        if element.attrib:
            result["@attributes"] = element.attrib
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()
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
        if not element.attrib and len(element) == 0:
            return element.text or ""
        return result

    def convert_xml_to_toml(self, xml_string: str) -> str:
        """Parses an XML string and returns a TOML string."""
        try:
            root = DefusedET.fromstring(xml_string)
            data = {root.tag: self._element_to_dict(root)}
            return tomlkit.dumps(data)
        except DefusedET.ParseError as e:
            raise ValueError(f"XML Parse Error: {e}")
        except Exception as e:
            raise ValueError(f"Error converting XML to TOML: {e}")

    def _dict_to_element(self, parent, data: Any) -> None:
        import xml.etree.ElementTree as ET
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
            for item in data:
                child = ET.SubElement(parent, "item")
                self._dict_to_element(child, item)
        else:
            if data is not None:
                parent.text = str(data)

    def convert_toml_to_xml(self, toml_string: str) -> str:
        """Parses a TOML string and returns an XML string."""
        import xml.etree.ElementTree as ET
        try:
            data = tomlkit.parse(toml_string).unwrap()
        except Exception as e:
            raise ValueError(f"TOML Parse Error: {e}")

        if not isinstance(data, dict):
            root = ET.Element("root")
            self._dict_to_element(root, data)
        elif len(data) == 1:
            root_key = list(data.keys())[0]
            root = ET.Element(root_key)
            self._dict_to_element(root, data[root_key])
        else:
            root = ET.Element("root")
            self._dict_to_element(root, data)

        try:
            ET.indent(root, space="  ", level=0)
        except AttributeError:
            pass

        return ET.tostring(root, encoding="unicode", xml_declaration=False)


def run_xml2toml_lab_logic(args):
    """CLI handler for Xml2Toml Lab."""
    manager = Xml2TomlManager()

    action = getattr(args, "action", None)
    if action not in ("xml2toml", "toml2xml"):
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

        if len(input_data) < 1000:
            path = Path(input_data)
            if path.exists() and path.is_file():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = input_data
        else:
            content = input_data

        if action == "xml2toml":
            result = manager.convert_xml_to_toml(content)
        else:
            result = manager.convert_toml_to_xml(content)

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
