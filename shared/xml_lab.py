import sys
import json
import defusedxml.ElementTree as DetusedET
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

class XmlLabManager:
    """
    Manages XML operations: format, validate, xpath, edit, to_json.
    """

    def parse(self, content: str) -> ET.Element:
        """Parses XML content string into an ElementTree Element."""
        try:
            return DetusedET.fromstring(content)
        except DetusedET.ParseError as e:
            raise ValueError(f"XML Parse Error: {e}")

    def load_file(self, filepath: str) -> ET.Element:
        """Loads XML from a file path."""
        try:
            tree = DetusedET.parse(filepath)
            return tree.getroot()
        except DetusedET.ParseError as e:
            raise ValueError(f"XML Parse Error in {filepath}: {e}")
        except FileNotFoundError:
            raise ValueError(f"File not found: {filepath}")

    def format(self, element: ET.Element) -> str:
        """Returns a pretty-printed XML string."""
        # Create a copy to avoid modifying the original tree if needed,
        # but here we just want the string.
        # indent was added in Python 3.9
        if sys.version_info >= (3, 9):
            ET.indent(element, space="  ", level=0)

        # maintain compatibility with older python if needed, but environment is 3.12
        return ET.tostring(element, encoding="unicode", method="xml")

    def validate(self, content: str) -> Optional[str]:
        """Returns None if valid, else error message."""
        try:
            DetusedET.fromstring(content)
            return None
        except DetusedET.ParseError as e:
            return str(e)

    def xpath(self, element: ET.Element, query: str) -> List[ET.Element]:
        """Finds elements matching the XPath query."""
        try:
            return element.findall(query)
        except SyntaxError as e:
            raise ValueError(f"Invalid XPath query: {e}")

    def edit(self, element: ET.Element, query: str, value: str, attribute: Optional[str] = None) -> int:
        """
        Modifies elements matching the XPath query.
        Returns the number of modified elements.
        """
        targets = self.xpath(element, query)
        count = 0
        for target in targets:
            if attribute:
                target.set(attribute, value)
            else:
                target.text = value
            count += 1
        return count

    def to_json(self, element: ET.Element) -> Dict[str, Any]:
        """Converts XML Element to a dictionary (naive conversion)."""
        result = {}

        # Attributes
        if element.attrib:
            result["@attributes"] = element.attrib

        # Text content
        if element.text and element.text.strip():
            result["#text"] = element.text.strip()

        # Children
        for child in element:
            child_data = self.to_json(child)
            tag = child.tag

            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(child_data)
                else:
                    result[tag] = [result[tag], child_data]
            else:
                result[tag] = child_data

        # If the element has no attributes and no children, just return the text
        if not element.attrib and len(element) == 0:
            return element.text or ""

        return result

def run_xml_lab_logic(args):
    """CLI Entry point for XML Lab."""
    manager = XmlLabManager()

    # Read Input
    content = ""
    root = None

    if args.input:
        try:
            if args.input == "-":
                content = sys.stdin.read()
                root = manager.parse(content)
            else:
                root = manager.load_file(args.input)
                # If we loaded from file, we might want content for validation too
                if args.action == "validate":
                    with open(args.input, 'r', encoding='utf-8') as f:
                        content = f.read()
        except Exception as e:
            print(f"Error loading input: {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
        try:
            root = manager.parse(content)
        except Exception as e:
            print(f"Error parsing input: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Input file or stdin required.", file=sys.stderr)
        sys.exit(1)

    # Actions
    if args.action == "format":
        print(manager.format(root))

    elif args.action == "validate":
        # If content wasn't loaded (e.g. input was a file path parsed directly into root),
        # we can't easily validate raw string unless we read it.
        # But parse() already validates structure.
        # So if we reached here with root, it is valid XML.
        print("✅ XML is valid.")

    elif args.action == "xpath":
        try:
            results = manager.xpath(root, args.query)
            if not results:
                print("No matches found.")
            for item in results:
                # If it's an Element, print it nicely
                if isinstance(item, ET.Element):
                    # For simple display, just print the tag and text or attributes
                    # Or full XML snippet
                    snippet = ET.tostring(item, encoding="unicode").strip()
                    print(snippet)
                else:
                    print(item)
        except Exception as e:
             print(f"Error executing XPath: {e}", file=sys.stderr)
             sys.exit(1)

    elif args.action == "edit":
        if not args.value:
             print("Error: --value required for edit.", file=sys.stderr)
             sys.exit(1)

        count = manager.edit(root, args.query, args.value, args.attr)
        print(f"Modified {count} element(s).")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(manager.format(root))
            print(f"✅ Saved to {args.output}")
        else:
            print(manager.format(root))

    elif args.action == "json":
        data = {root.tag: manager.to_json(root)}
        print(json.dumps(data, indent=2))

    sys.exit(0)
