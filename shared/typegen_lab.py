"""
Typegen Lab
===========

Generates data structure definitions (e.g. Go structs, TypeScript interfaces, Python dataclasses, Rust structs) from JSON.
"""

import json
from typing import Any, Dict





class TypegenManager:
    """Manages the generation of types from JSON."""

    def _get_type_name(self, key: str) -> str:
        """Converts snake_case or camelCase to PascalCase."""
        if not key:
            return "UnknownType"
        # Split by underscore or hyphen
        parts = key.replace("-", "_").split("_")
        name = "".join(p.capitalize() for p in parts)
        return name

    def generate(self, json_str: str, root_name: str = "Root", lang: str = "typescript") -> str:
        """Generates types from a JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return f"Error parsing JSON: {e}"

        if not isinstance(data, (dict, list)):
            return "Root JSON element must be an object or array."

        # A map of generated structures. Key is struct name, value is string definition.
        self.structs = {}

        # If it's a list, generate from the first item or merge types. For simplicity, take first.
        if isinstance(data, list):
            if not data:
                return "Empty array."
            data = data[0]
            if not isinstance(data, dict):
                return "Root array must contain objects."

        self._parse_dict(data, root_name, lang)

        return "\n\n".join(self.structs.values())

    def _parse_dict(self, data: Dict[str, Any], name: str, lang: str):
        if lang == "typescript":
            self._generate_typescript(data, name)
        elif lang == "go":
            self._generate_go(data, name)
        elif lang == "python":
            self._generate_python(data, name)
        elif lang == "rust":
            self._generate_rust(data, name)
        else:
            self.structs["Error"] = f"Unsupported language: {lang}"

    def _get_value_type(self, val: Any, key: str, lang: str) -> str:
        if val is None:
            return "any" if lang == "typescript" else "interface{}" if lang == "go" else "Any" if lang == "python" else "Option<serde_json::Value>"

        if isinstance(val, bool):
            return "boolean" if lang == "typescript" else "bool" if lang == "go" else "bool" if lang == "python" else "bool"

        if isinstance(val, int):
            return "number" if lang == "typescript" else "int" if lang == "go" else "int" if lang == "python" else "i64"

        if isinstance(val, float):
            return "number" if lang == "typescript" else "float64" if lang == "go" else "float" if lang == "python" else "f64"

        if isinstance(val, str):
            return "string" if lang == "typescript" else "string" if lang == "go" else "str" if lang == "python" else "String"

        if isinstance(val, dict):
            nested_name = self._get_type_name(key)
            self._parse_dict(val, nested_name, lang)
            return nested_name if lang != "go" else f"*{nested_name}"

        if isinstance(val, list):
            if not val:
                base = "any" if lang == "typescript" else "interface{}" if lang == "go" else "Any" if lang == "python" else "serde_json::Value"
            else:
                base = self._get_value_type(val[0], key, lang)

            if lang == "typescript":
                return f"{base}[]"
            elif lang == "go":
                return f"[]{base}"
            elif lang == "python":
                return f"List[{base}]"
            elif lang == "rust":
                return f"Vec<{base}>"

        return "any" if lang == "typescript" else "interface{}" if lang == "go" else "Any" if lang == "python" else "serde_json::Value"

    def _generate_typescript(self, data: Dict[str, Any], name: str):
        lines = [f"export interface {name} {{"]
        for key, val in data.items():
            ts_type = self._get_value_type(val, key, "typescript")
            lines.append(f"  {key}: {ts_type};")
        lines.append("}")
        self.structs[name] = "\n".join(lines)

    def _generate_go(self, data: Dict[str, Any], name: str):
        lines = [f"type {name} struct {{"]
        for key, val in data.items():
            field_name = self._get_type_name(key)
            go_type = self._get_value_type(val, key, "go")
            lines.append(f"  {field_name} {go_type} `json:\"{key}\"`")
        lines.append("}")
        self.structs[name] = "\n".join(lines)

    def _generate_python(self, data: Dict[str, Any], name: str):
        lines = ["@dataclass", f"class {name}:"]
        if not data:
            lines.append("    pass")
        for key, val in data.items():
            py_type = self._get_value_type(val, key, "python")
            # If key is not a valid identifier, this might need aliasing, but we'll assume valid identifiers for basic dataclasses
            # Pydantic or alias would be needed for complex keys, we'll keep it simple here.
            safe_key = key.replace("-", "_")
            lines.append(f"    {safe_key}: {py_type}")
        # Make sure we add dataclass import if needed
        self.structs[name] = "\n".join(lines)

    def _generate_rust(self, data: Dict[str, Any], name: str):
        lines = ["#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]", "#[serde(rename_all = \"camelCase\")]", f"pub struct {name} {{"]
        for key, val in data.items():
            safe_key = key.replace("-", "_")
            if safe_key in ["type", "match", "loop", "fn", "let"]:  # rust keywords
                safe_key = f"r#{safe_key}"

            rs_type = self._get_value_type(val, key, "rust")

            if safe_key != key:
                lines.append(f"    #[serde(rename = \"{key}\")]")

            lines.append(f"    pub {safe_key}: {rs_type},")
        lines.append("}")
        self.structs[name] = "\n".join(lines)





def run_typegen_lab_logic(args):
    """CLI logic for typegen-lab."""
    manager = TypegenManager()

    json_str = ""
    if hasattr(args, "file") and args.file:
        try:
            with open(args.file, "r") as f:
                json_str = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return False
    elif hasattr(args, "json") and args.json:
        json_str = args.json
    else:
        # read from stdin
        import sys
        if not sys.stdin.isatty():
            json_str = sys.stdin.read()
        else:
            print("Please provide JSON via --file, --json, or stdin.")
            return False

    if not json_str.strip():
        print("No JSON data provided.")
        return False

    result = manager.generate(json_str, root_name=args.name, lang=args.lang)

    if hasattr(args, "output") and args.output:
        try:
            with open(args.output, "w") as f:
                if args.lang == "python" and "dataclass" in result:
                    f.write("from dataclasses import dataclass\nfrom typing import Any, List\n\n")
                elif args.lang == "rust" and "serde" in result:
                    f.write("use serde::{Serialize, Deserialize};\n\n")
                f.write(result)
            print(f"✅ Generated types saved to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            return False
    else:
        if args.lang == "python" and "dataclass" in result:
            print("from dataclasses import dataclass\nfrom typing import Any, List\n")
        elif args.lang == "rust" and "serde" in result:
            print("use serde::{Serialize, Deserialize};\n")
        print(result)

    return True
