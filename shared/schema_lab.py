import json
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

class SchemaLabManager:
    """
    Manages schema inference and conversion.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def infer_schema(self, data: Any) -> Dict[str, Any]:
        """
        Infers a JSON Schema from a Python object (dict, list, etc.).
        """
        if data is None:
            return {"type": "null"}
        elif isinstance(data, bool):
            return {"type": "boolean"}
        elif isinstance(data, int):
            return {"type": "integer"}
        elif isinstance(data, float):
            return {"type": "number"}
        elif isinstance(data, str):
            return {"type": "string"}
        elif isinstance(data, list):
            schema = {"type": "array"}
            if data:
                # Infer schema for all items and merge
                item_schemas = [self.infer_schema(item) for item in data]
                # Simple merge: if all are same, use one. Else use "anyOf"
                # For MVP, we'll take the first non-null one or mix
                # Better: check if all are same type
                first_type = item_schemas[0].get("type")
                if all(s.get("type") == first_type for s in item_schemas):
                     if first_type == "object":
                         # Merge object properties
                         merged_props = {}
                         for s in item_schemas:
                             for k, v in s.get("properties", {}).items():
                                 if k not in merged_props:
                                     merged_props[k] = v
                                 # TODO: Handle conflict
                         schema["items"] = {"type": "object", "properties": merged_props}
                     else:
                         schema["items"] = item_schemas[0]
                else:
                    # distinct schemas
                    # remove duplicates based on json repr
                    unique = []
                    seen = set()
                    for s in item_schemas:
                        r = json.dumps(s, sort_keys=True)
                        if r not in seen:
                            seen.add(r)
                            unique.append(s)
                    if len(unique) == 1:
                         schema["items"] = unique[0]
                    else:
                         schema["items"] = {"anyOf": unique}
            return schema
        elif isinstance(data, dict):
            props = {}
            for k, v in data.items():
                props[k] = self.infer_schema(v)
            return {"type": "object", "properties": props}
        else:
            return {}

    def to_typescript(self, schema: Dict[str, Any], root_name: str = "Root") -> str:
        """
        Converts JSON Schema to TypeScript interfaces.
        """
        lines = []
        interfaces = {} # name -> content

        def _resolve_type(s: Dict[str, Any], name: str) -> str:
            t = s.get("type")
            if t == "string":
                return "string"
            elif t == "integer" or t == "number":
                return "number"
            elif t == "boolean":
                return "boolean"
            elif t == "null":
                return "null"
            elif t == "array":
                items = s.get("items", {})
                item_type = _resolve_type(items, f"{name}Item")
                if " | " in item_type: # parenthesize union types
                    return f"({item_type})[]"
                return f"{item_type}[]"
            elif t == "object":
                # Create interface
                iface_name = name
                props = s.get("properties", {})
                content = []
                for pk, pv in props.items():
                    pt = _resolve_type(pv, f"{name}{pk.capitalize()}")
                    content.append(f"  {pk}: {pt};")

                interfaces[iface_name] = "{\n" + "\n".join(content) + "\n}"
                return iface_name
            elif "anyOf" in s:
                types = [_resolve_type(sub, f"{name}Option{i}") for i, sub in enumerate(s["anyOf"])]
                return " | ".join(types)
            return "any"

        _resolve_type(schema, root_name)

        # Output interfaces in order (maybe reverse to define deps first? TS handles hoisting though)
        for name, content in interfaces.items():
            lines.append(f"export interface {name} {content}")

        return "\n\n".join(lines)

    def to_pydantic(self, schema: Dict[str, Any], root_name: str = "Root") -> str:
        """
        Converts JSON Schema to Pydantic models.
        """
        lines = ["from typing import List, Optional, Union, Any", "from pydantic import BaseModel", ""]
        models = {} # name -> list of lines

        def _resolve_type(s: Dict[str, Any], name: str) -> str:
            t = s.get("type")
            if t == "string":
                return "str"
            elif t == "integer":
                return "int"
            elif t == "number":
                return "float"
            elif t == "boolean":
                return "bool"
            elif t == "null":
                return "None"
            elif t == "array":
                items = s.get("items", {})
                item_type = _resolve_type(items, f"{name}Item")
                return f"List[{item_type}]"
            elif t == "object":
                model_name = name
                props = s.get("properties", {})
                field_lines = []
                for pk, pv in props.items():
                    pt = _resolve_type(pv, f"{name}{pk.capitalize()}")
                    # For simplicity, make everything Optional in this MVP inference
                    field_lines.append(f"    {pk}: Optional[{pt}] = None")

                if not field_lines:
                     field_lines.append("    pass")

                models[model_name] = [f"class {model_name}(BaseModel):"] + field_lines
                return model_name
            elif "anyOf" in s:
                types = [_resolve_type(sub, f"{name}Option{i}") for i, sub in enumerate(s["anyOf"])]
                # Filter out duplicates and None
                types = list(set(types))
                if len(types) == 1:
                    return types[0]
                return f"Union[{', '.join(types)}]"
            return "Any"

        _resolve_type(schema, root_name)

        # Output models. We need to respect order (deps first).
        # Python needs definition before use.
        # Simple topological sort or just reverse insertion might not work perfectly without a graph.
        # For MVP, let's output them and hope for the best, or use ForwardRefs (strings).
        # Actually Pydantic supports string forward refs. But better to define if possible.
        # Let's just output them in the order they were collected (leaves first usually due to recursion).

        # Wait, the recursion _resolve_type calls children *before* returning name.
        # So children are added to `models` *before* parents.
        # This matches Python's requirement!

        for name, content_lines in models.items():
            lines.extend(content_lines)
            lines.append("")

        return "\n".join(lines)


def run_schema_lab_logic(args):
    """
    CLI entry point for Schema Lab.
    """
    manager = SchemaLabManager(args.project_dir)

    if args.action == "infer":
        source_file = Path(args.file)
        if not source_file.exists():
            print(f"Error: File {source_file} not found.")
            sys.exit(1)

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                if source_file.suffix == '.json':
                    data = json.load(f)
                elif source_file.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    print("Error: Only JSON/YAML supported for inference.")
                    sys.exit(1)

            schema = manager.infer_schema(data)

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(schema, f, indent=2)
                print(f"✅ Schema saved to {args.output}")
            else:
                print(json.dumps(schema, indent=2))

        except Exception as e:
            print(f"Error during inference: {e}")
            sys.exit(1)

    elif args.action == "convert":
        source_file = Path(args.file)
        if not source_file.exists():
             print(f"Error: File {source_file} not found.")
             sys.exit(1)

        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            root_name = args.name or "Root"

            if args.format == "ts":
                result = manager.to_typescript(schema, root_name)
            elif args.format == "pydantic":
                result = manager.to_pydantic(schema, root_name)
            else:
                print(f"Error: Unknown format {args.format}")
                sys.exit(1)

            if args.output:
                 with open(args.output, 'w') as f:
                     f.write(result)
                 print(f"✅ Converted schema saved to {args.output}")
            else:
                 print(result)

        except Exception as e:
            print(f"Error during conversion: {e}")
            sys.exit(1)
    else:
        print(f"Unknown action: {args.action}")
        sys.exit(1)
