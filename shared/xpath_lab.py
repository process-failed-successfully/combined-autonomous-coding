"""
XPath Lab
=========

Utilities for evaluating XPath expressions against XML data.
"""

import sys
import xml.etree.ElementTree as pyET  # nosec B405
from typing import Dict, Any
from pathlib import Path

# Use defusedxml for safe parsing to avoid Bandit vulnerabilities (B314, B405)
import defusedxml.ElementTree as ET


class XpathLabManager:
    """Manages XPath evaluation operations."""

    def evaluate(self, xml_data: str, expression: str) -> Dict[str, Any]:
        """
        Evaluates an XPath expression against XML data.

        Args:
            xml_data: The XML string to query.
            expression: The XPath expression.

        Returns:
            A dictionary containing the 'success' status, 'result' list of matches, or an 'error' message.
        """
        if not xml_data or not xml_data.strip():
            return {"success": False, "error": "Empty XML data provided"}

        if not expression or not expression.strip():
            return {"success": False, "error": "Empty XPath expression provided"}

        try:
            # Parse safely
            root = ET.fromstring(xml_data)

            # Find matching elements using ElementTree's subset of XPath
            matches = root.findall(expression)

            # Helper to recursively convert Element to dict/string for generic display
            def elem_to_dict(elem):
                # If element has no children and has text, just return text (or dict if it has attributes)
                # For simplicity in this lab, return string representation or a dict with tag/text/attribs
                # if there are children.
                d = {"tag": elem.tag}
                if elem.text and elem.text.strip():
                    d["text"] = elem.text.strip()
                if elem.attrib:
                    d["attributes"] = elem.attrib
                children = list(elem)
                if children:
                    d["children"] = [elem_to_dict(c) for c in children]
                return d

            results = []
            for match in matches:
                results.append(elem_to_dict(match))

            return {
                "success": True,
                "result": results
            }

        except pyET.ParseError as e:
            return {"success": False, "error": f"Invalid XML: {e}"}
        except SyntaxError as e:
            # ElementTree throws SyntaxError for invalid XPath
            return {"success": False, "error": f"Invalid XPath expression: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_xpath_lab_logic(args) -> bool:
    """Entry point for the XPath Lab CLI."""
    manager = XpathLabManager()

    xml_data = ""

    # Read from file or stdin
    if args.input == "-":
        if sys.stdin.isatty():
            print("Error: No input provided on stdin.", file=sys.stderr)
            return False
        xml_data = sys.stdin.read()
    else:
        path = Path(args.input)
        if not path.is_file():
            print(f"Error: File '{args.input}' not found.", file=sys.stderr)
            return False
        xml_data = path.read_text(encoding='utf-8')

    result = manager.evaluate(xml_data, args.expression)

    if result["success"]:
        import json
        print(json.dumps(result["result"], indent=2))
        return True
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return False
