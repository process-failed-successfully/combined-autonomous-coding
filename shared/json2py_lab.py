import sys
import json
import argparse
from typing import Dict, Any, List

class Json2PyManager:
    """Manager for converting JSON string to Python dataclass or Pydantic models."""

    def __init__(self):
        self.class_definitions = []
        self.class_names = set()

    def generate(self, json_str: str, framework: str = "dataclass", root_name: str = "RootModel") -> str:
        self.class_definitions = []
        self.class_names = set()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            # If the root is a list, try to infer from the first element
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                data = data[0]
            else:
                raise ValueError("JSON root must be an object or a list of objects.")

        self._parse_dict(data, root_name, framework)

        # Note: Child classes are appended first (since we parse children recursively before the parent).
        # This guarantees dependent types are defined before they are used.

        imports = ""
        if framework == "dataclass":
            imports = "from dataclasses import dataclass\nfrom typing import Any, List, Optional\n\n"
        elif framework == "pydantic":
            imports = "from pydantic import BaseModel\nfrom typing import Any, List, Optional\n\n"
        elif framework == "msgspec":
            imports = "from msgspec import Struct\nfrom typing import Any, List, Optional\n\n"
        elif framework == "typeddict":
            imports = "from typing import Any, List, Optional, TypedDict\n\n"

        return imports + "\n\n".join(self.class_definitions)

    def _parse_dict(self, data: Dict[str, Any], class_name: str, framework: str):
        # Handle duplicate class names recursively
        original_class_name = class_name
        counter = 1
        while class_name in self.class_names:
            class_name = f"{original_class_name}{counter}"
            counter += 1

        self.class_names.add(class_name)

        fields = []
        for key, value in data.items():
            py_type = self._infer_type(key, value, framework)
            # Make sure key is valid python identifier
            safe_key = self._sanitize_identifier(key)
            fields.append((safe_key, py_type))

        if framework == "dataclass":
            class_def = f"@dataclass\nclass {class_name}:\n"
        elif framework == "pydantic":
            class_def = f"class {class_name}(BaseModel):\n"
        elif framework == "msgspec":
            class_def = f"class {class_name}(Struct):\n"
        elif framework == "typeddict":
            class_def = f"class {class_name}(TypedDict, total=False):\n"
        else:
            raise ValueError(f"Unknown framework: {framework}")

        if not fields:
            class_def += "    pass\n"
        else:
            for name, type_str in fields:
                if framework == "typeddict":
                    class_def += f"    {name}: {type_str}\n"
                else:
                    class_def += f"    {name}: Optional[{type_str}] = None\n"

        self.class_definitions.append(class_def.rstrip())

    def _infer_type(self, key: str, value: Any, framework: str) -> str:
        if value is None:
            return "Any"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif isinstance(value, list):
            if len(value) == 0:
                return "List[Any]"
            else:
                # Infer type from first element
                first_elem = value[0]
                if isinstance(first_elem, dict):
                    child_class_name = self._to_pascal_case(key) + "Item"
                    self._parse_dict(first_elem, child_class_name, framework)
                    return f"List[{child_class_name}]"
                else:
                    item_type = self._infer_type(key, first_elem, framework)
                    return f"List[{item_type}]"
        elif isinstance(value, dict):
            child_class_name = self._to_pascal_case(key)
            self._parse_dict(value, child_class_name, framework)
            return child_class_name
        else:
            return "Any"

    def _to_pascal_case(self, s: str) -> str:
        # replace non-alphanumeric with space
        s = "".join([c if c.isalnum() else " " for c in s])
        words = s.split()
        if not words:
            return "NestedClass"
        return "".join(w.capitalize() for w in words)

    def _sanitize_identifier(self, s: str) -> str:
        if not s:
            return "field"
        # replace non-alphanumeric with underscore
        s = "".join([c if c.isalnum() else "_" for c in s])
        # cannot start with number
        if s[0].isdigit():
            s = "_" + s
        # python keywords check
        import keyword
        if keyword.iskeyword(s):
            s += "_"
        return s

def run_json2py_lab_logic(args) -> bool:
    """CLI logic for the Json2Py lab."""
    import sys
    manager = Json2PyManager()

    input_data = ""
    if getattr(args, 'file', None):
        try:
            with open(args.file, 'r') as f:
                input_data = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif getattr(args, 'text', None):
        input_data = args.text
    elif not sys.stdin.isatty():
        try:
            input_data = sys.stdin.read()
        except Exception:
            pass

    if not input_data:
        print("Error: No JSON input provided via --file, --text, or stdin.", file=sys.stderr)
        return False

    framework = getattr(args, 'framework', 'dataclass')
    root_name = getattr(args, 'name', 'RootModel')

    try:
        output = manager.generate(input_data, framework=framework, root_name=root_name)
    except ValueError as e:
        print(f"Error generating Python code: {e}", file=sys.stderr)
        return False

    if getattr(args, 'output', None):
        try:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Code saved to {args.output}")
        except Exception as e:
            print(f"Error saving to file: {e}", file=sys.stderr)
            return False
    else:
        print(output)

    return True
