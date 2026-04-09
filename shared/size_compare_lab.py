import sys
import json
from typing import Optional

def dict_to_xml(tag: str, d: dict):
    import xml.etree.ElementTree as ET # nosec B405
    """Helper to convert a dict to an XML element."""
    elem = ET.Element(tag)
    for key, val in d.items():
        child = ET.Element(str(key))
        if isinstance(val, dict):
            child.append(dict_to_xml(str(key), val))
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    child.append(dict_to_xml("item", item))
                else:
                    item_elem = ET.Element("item")
                    item_elem.text = str(item)
                    child.append(item_elem)
        else:
            child.text = str(val)
        elem.append(child)
    return elem

class SizeCompareManager:
    """Compares the byte sizes of data serialized into different formats."""

    def compare_sizes(self, json_data: str) -> str:
        """
        Parses JSON data and serializes it to JSON, YAML, TOML, MsgPack, CBOR, BSON, and XML.
        Returns a formatted string representing the byte sizes.
        """
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON input. {e}"

        results = []

        # 1. JSON
        try:
            json_bytes = json.dumps(data, separators=(',', ':')).encode('utf-8')
            results.append(("JSON", len(json_bytes)))
        except Exception:
            results.append(("JSON", "Failed"))

        # 2. YAML
        try:
            import yaml
            yaml_bytes = yaml.safe_dump(data, default_flow_style=False).encode('utf-8')
            results.append(("YAML", len(yaml_bytes)))
        except ImportError:
            results.append(("YAML", "N/A (pyyaml missing)"))
        except Exception:
            results.append(("YAML", "Failed"))

        # 3. TOML
        try:
            import tomlkit
            if isinstance(data, dict):
                toml_bytes = tomlkit.dumps(data).encode('utf-8')
                results.append(("TOML", len(toml_bytes)))
            else:
                results.append(("TOML", "N/A (Requires Object root)"))
        except ImportError:
            results.append(("TOML", "N/A (tomlkit missing)"))
        except Exception:
            results.append(("TOML", "Failed"))

        # 4. MsgPack
        try:
            import msgpack
            msgpack_bytes = msgpack.packb(data)
            results.append(("MsgPack", len(msgpack_bytes)))
        except ImportError:
            results.append(("MsgPack", "N/A (msgpack missing)"))
        except Exception:
            results.append(("MsgPack", "Failed"))

        # 5. CBOR
        try:
            import cbor2
            cbor_bytes = cbor2.dumps(data)
            results.append(("CBOR", len(cbor_bytes)))
        except ImportError:
            results.append(("CBOR", "N/A (cbor2 missing)"))
        except Exception:
            results.append(("CBOR", "Failed"))

        # 6. BSON
        try:
            import bson
            if isinstance(data, dict):
                bson_bytes = bson.encode(data)
                results.append(("BSON", len(bson_bytes)))
            else:
                results.append(("BSON", "N/A (Requires Object root)"))
        except ImportError:
            results.append(("BSON", "N/A (pymongo missing)"))
        except Exception:
            results.append(("BSON", "Failed"))

        # 7. XML
        try:
            import xml.etree.ElementTree as ET # nosec B405
            if isinstance(data, dict):
                root = dict_to_xml("root", data)
                xml_str = ET.tostring(root, encoding='unicode')
                xml_bytes = xml_str.encode('utf-8')
                results.append(("XML", len(xml_bytes)))
            else:
                results.append(("XML", "N/A (Requires Object root)"))
        except ImportError:
            results.append(("XML", "N/A (xml missing)"))
        except Exception:
            results.append(("XML", "Failed"))

        # Format output as a text table
        header = f"{'Format':<15} | {'Size (bytes)':<15}"
        output = [header, "-" * 33]

        # Sort by size (if it's an integer)
        def sort_key(item):
            val = item[1]
            return val if isinstance(val, int) else float('inf')

        results.sort(key=sort_key)

        for fmt, size in results:
            output.append(f"{fmt:<15} | {str(size):<15}")

        return "\n".join(output)

def run_size_compare_lab_logic(args) -> bool:
    """CLI logic for Size Compare Lab."""
    manager = SizeCompareManager()

    data = None
    if getattr(args, 'file', None):
        import pathlib
        path = pathlib.Path(args.file)
        if not path.exists():
            print(f"Error: File {path} not found.", file=sys.stderr)
            return False
        data = path.read_text(encoding="utf-8")
    elif getattr(args, 'text', None):
        data = args.text
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            data = sys.stdin.read()
        else:
            print("Error: Input text or file required.", file=sys.stderr)
            return False

    if not data or not data.strip():
        print("Error: Empty input.", file=sys.stderr)
        return False

    result = manager.compare_sizes(data)
    print(result)
    return True
