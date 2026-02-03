import json
import yaml
import csv
import defusedxml.ElementTree as ET
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

class DataLabManager:
    """
    Manages data format conversion, validation, and analysis.
    Supported formats: JSON, YAML, CSV (limited), XML (limited).
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def load_data(self, file_path: Path) -> Any:
        """
        Loads data from a file based on its extension.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if ext == '.json':
                    return json.load(f)
                elif ext in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif ext == '.csv':
                    reader = csv.DictReader(f)
                    return list(reader)
                elif ext == '.xml':
                    tree = ET.parse(f)
                    return self._xml_to_dict(tree.getroot())
                else:
                    raise ValueError(f"Unsupported file extension: {ext}")
        except Exception as e:
            raise ValueError(f"Error loading {file_path}: {e}")

    def save_data(self, data: Any, file_path: Path, format: str) -> None:
        """
        Saves data to a file in the specified format.
        """
        format = format.lower()
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                if format == 'json':
                    json.dump(data, f, indent=2)
                elif format == 'yaml':
                    yaml.dump(data, f, sort_keys=False)
                elif format == 'csv':
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
                    else:
                        raise ValueError("Data must be a list of dictionaries for CSV export.")
                elif format == 'xml':
                    if isinstance(data, dict):
                        root_name = list(data.keys())[0] if len(data) == 1 else "root"
                        content = data[root_name] if len(data) == 1 else data
                        root = ET.Element(root_name)
                        self._dict_to_xml(root, content)
                        tree = ET.ElementTree(root)
                        tree.write(f, encoding='unicode', xml_declaration=True)
                    else:
                        raise ValueError("Data must be a dictionary for XML export.")
                else:
                    raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            raise ValueError(f"Error saving to {file_path}: {e}")

    def convert(self, source_file: Path, target_format: str, output_file: Optional[Path] = None) -> str:
        """
        Converts a file to another format. Returns the result as a string if no output file is provided.
        """
        data = self.load_data(source_file)

        if output_file:
            self.save_data(data, output_file, target_format)
            return f"Successfully converted {source_file} to {target_format} and saved to {output_file}"
        else:
            # Return as string
            if target_format == 'json':
                return json.dumps(data, indent=2)
            elif target_format == 'yaml':
                return yaml.dump(data, sort_keys=False)
            elif target_format == 'csv':
                # Return CSV string
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    import io
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    return output.getvalue()
                else:
                    raise ValueError("Data must be a list of dictionaries for CSV conversion.")
            # XML string is a bit tricky without a file, but let's try
            elif target_format == 'xml':
                import io
                if isinstance(data, dict):
                    root_name = list(data.keys())[0] if len(data) == 1 else "root"
                    content = data[root_name] if len(data) == 1 else data
                    root = ET.Element(root_name)
                    self._dict_to_xml(root, content)
                    # Use standard library tostring, but it returns bytes or string depending on encoding
                    # We want string
                    # Use standard library tostring, but it returns bytes or string depending on encoding
                    # We want string
                    # defusedxml does not have tostring, so we use the safe ET we imported
                    return ET.tostring(root, encoding='unicode')
                else:
                    raise ValueError("Data must be a dictionary for XML conversion.")
            else:
                raise ValueError(f"Unsupported format: {target_format}")

    def validate(self, file_path: Path, schema_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Validates a file's syntax and optionally against a schema (JSON only for now).
        """
        result = {"valid": False, "message": ""}
        try:
            data = self.load_data(file_path)

            if schema_path:
                if file_path.suffix.lower() == '.json' and schema_path.suffix.lower() == '.json':
                    try:
                        import jsonschema # Might not be installed, check first
                        with open(schema_path, 'r') as f:
                            schema = json.load(f)
                        jsonschema.validate(instance=data, schema=schema)
                        result["valid"] = True
                        result["message"] = "Valid JSON syntax and schema."
                    except ImportError:
                        result["message"] = "jsonschema library not found. Please install it to validate against schemas."
                    except Exception as e:
                        result["message"] = f"Schema validation failed: {e}"
                else:
                    result["valid"] = True
                    result["message"] = "Syntax valid. Schema validation skipped (only JSON supported)."
            else:
                result["valid"] = True
                result["message"] = "Syntax valid."

        except Exception as e:
            result["message"] = f"Validation failed: {e}"

        return result

    def get_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Returns statistics about the data.
        """
        data = self.load_data(file_path)

        info = {
            "type": type(data).__name__,
            "size_bytes": file_path.stat().st_size,
        }

        if isinstance(data, list):
            info["items"] = len(data)
            if data and isinstance(data[0], dict):
                info["keys_per_item"] = len(data[0].keys())
        elif isinstance(data, dict):
            info["keys"] = len(data.keys())
            info["depth"] = self._get_depth(data)

        return info

    def _get_depth(self, d, level=0):
        if not isinstance(d, dict) or not d:
            return level
        return max(self._get_depth(v, level + 1) for k, v in d.items())

    def _xml_to_dict(self, element) -> Any:
        result: Dict[str, Any] = {}
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                if isinstance(result[child.tag], list):
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = [result[child.tag], child_data]
            else:
                result[child.tag] = child_data

        # If no children, use text
        if not result:
            return element.text or ""
        return result

    def _dict_to_xml(self, parent, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        child = ET.SubElement(parent, k)
                        self._dict_to_xml(child, item)
                else:
                    child = ET.SubElement(parent, k)
                    self._dict_to_xml(child, v)
        elif isinstance(data, list):
            # Should not happen if called correctly (parent is element)
            pass
        else:
            parent.text = str(data)

def run_data_lab_logic(args):
    """
    CLI entry point for Data Lab.
    """
    manager = DataLabManager(args.project_dir)

    if args.action == "convert":
        source = Path(args.source)
        output = Path(args.output) if args.output else None
        target_format = args.target_format

        try:
            convert_result = manager.convert(source, target_format, output)
            print(convert_result)
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "validate":
        file_path = Path(args.file)
        schema_path = Path(args.schema) if args.schema else None

        validate_result = manager.validate(file_path, schema_path)
        if validate_result["valid"]:
            print(f"✅ {validate_result['message']}")
        else:
            print(f"❌ {validate_result['message']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "info":
        file_path = Path(args.file)
        try:
            info_dict = manager.get_info(file_path)
            print(f"--- Data Info: {file_path.name} ---")
            for k, v in info_dict.items():
                print(f"  {k}: {v}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
