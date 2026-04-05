import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from io import StringIO


class Csv2XmlManager:
    """Manages CSV to XML conversion."""

    def convert_string(self, csv_string: str, delimiter: str = ",", root_tag: str = "root", row_tag: str = "row") -> str:
        """Converts a CSV string to an XML string."""
        if not csv_string.strip():
            return f"<{root_tag}></{root_tag}>"

        try:
            f = StringIO(csv_string)
            reader = csv.DictReader(f, delimiter=delimiter)

            root = ET.Element(root_tag)

            for row in reader:
                item = ET.SubElement(root, row_tag)
                for key, value in row.items():
                    # Handle empty/missing headers
                    safe_key = str(key).strip() if key else "column"
                    if not safe_key:
                        safe_key = "column"
                    # Make tag names safe for XML (replace spaces, etc)
                    safe_key = "".join([c if c.isalnum() or c in "_-" else "_" for c in safe_key])
                    # XML tags cannot start with a number or punctuation except _
                    if not safe_key[0].isalpha() and safe_key[0] != '_':
                        safe_key = "_" + safe_key

                    child = ET.SubElement(item, safe_key)
                    child.text = str(value) if value is not None else ""

            try:
                # Pretty print (Python 3.9+)
                ET.indent(root, space="  ", level=0)
            except AttributeError:
                pass  # fallback if python version < 3.9

            return ET.tostring(root, encoding="unicode", xml_declaration=False)

        except Exception as e:
            raise ValueError(f"Error converting CSV to XML: {e}")

    def convert_file(self, filepath: Path, delimiter: str = ",", root_tag: str = "root", row_tag: str = "row") -> str:
        """Converts a CSV file to an XML string."""
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                csv_string = f.read()
            return self.convert_string(csv_string, delimiter, root_tag, row_tag)
        except Exception as e:
            raise ValueError(f"Error reading or parsing {filepath}: {e}")


def run_csv2xml_lab_logic(args):
    """CLI handler for Csv2Xml Lab."""
    manager = Csv2XmlManager()

    delimiter = getattr(args, "delimiter", ",")
    root_tag = getattr(args, "root_tag", "root")
    row_tag = getattr(args, "row_tag", "row")

    try:
        if getattr(args, "file", None):
            filepath = Path(args.file)
            xml_output = manager.convert_file(filepath, delimiter, root_tag, row_tag)
        elif getattr(args, "text", None):
            xml_output = manager.convert_string(args.text, delimiter, root_tag, row_tag)
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
            xml_output = manager.convert_string(content, delimiter, root_tag, row_tag)
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
