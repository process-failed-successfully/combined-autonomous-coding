import sys
import yaml
import argparse
import xml.etree.ElementTree as ET  # nosec B405
from xml.dom import minidom  # nosec B408
from pathlib import Path
from typing import Dict, Any, Union

class Yaml2XmlManager:
    """Manages conversion between YAML and XML."""

    def convert(self, yaml_data: Union[str, Dict[str, Any]], root_name: str = "root") -> str:
        """Converts YAML string or dictionary to XML string."""
        if isinstance(yaml_data, str):
            try:
                data = yaml.safe_load(yaml_data)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML data: {e}")
        else:
            data = yaml_data

        if data is None:
            data = {}

        # Build XML
        root = ET.Element(root_name)
        self._build_xml(root, data)

        # Generate pretty XML
        xml_str = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(xml_str)  # nosec B318
        pretty_xml = parsed.toprettyxml(indent="  ")

        # Strip the <?xml ... ?> declaration to be consistent with some other labs,
        # but standard xml.dom.minidom toprettyxml adds it. We'll leave it as is
        # or strip empty lines.
        # Let's clean up empty lines minidom sometimes adds.
        return "\n".join([line for line in pretty_xml.split("\n") if line.strip()])

    def _build_xml(self, parent: ET.Element, data: Any):
        """Recursively builds XML elements."""
        if isinstance(data, dict):
            for key, val in data.items():
                # Ensure valid XML tag name (basic cleanup)
                tag_name = str(key).replace(" ", "_").replace("/", "_")

                # If it's a list, we might want multiple elements with the same tag,
                # but to be safe and deterministic, let's wrap list items in <item>.
                # Alternatively, we could create multiple `<tag_name>` elements.
                # Standard practice for json/yaml to xml is either:
                # <key><item>...</item><item>...</item></key>
                if isinstance(val, list):
                    list_elem = ET.SubElement(parent, tag_name)
                    for item in val:
                        item_elem = ET.SubElement(list_elem, "item")
                        self._build_xml(item_elem, item)
                else:
                    child = ET.SubElement(parent, tag_name)
                    self._build_xml(child, val)
        elif isinstance(data, list):
            for item in data:
                item_elem = ET.SubElement(parent, "item")
                self._build_xml(item_elem, item)
        else:
            if data is not None:
                parent.text = str(data)

def run_yaml2xml_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for YAML to XML conversion."""
    manager = Yaml2XmlManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        import asyncio
        print("Launching YAML to XML Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-yaml2xml")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        return True

    yaml_text = ""
    if getattr(args, "file", None):
        try:
            yaml_text = Path(args.file).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        yaml_text = args.text
    elif not sys.stdin.isatty():
        yaml_text = sys.stdin.read()
    else:
        print("Error: No input provided. Use --file, --text, or pass via stdin.", file=sys.stderr)
        return False

    if not yaml_text.strip():
        print("Error: Empty input data.", file=sys.stderr)
        return False

    try:
        xml_result = manager.convert(yaml_text, root_name=getattr(args, "root", "root"))
    except Exception as e:
        print(f"Error converting YAML to XML: {e}", file=sys.stderr)
        return False

    if getattr(args, "output", None):
        try:
            Path(args.output).write_text(xml_result, encoding="utf-8")
            print(f"✅ Successfully wrote XML to {args.output}")
        except Exception as e:
            print(f"Error writing to file {args.output}: {e}", file=sys.stderr)
            return False
    else:
        print(xml_result)

    return True
