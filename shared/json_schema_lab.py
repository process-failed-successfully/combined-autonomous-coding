import sys
import json
from typing import Any, Dict

try:
    import jsonschema
except ImportError:
    jsonschema = None


class JsonSchemaManager:
    """Manages the generation and validation of JSON Schema from JSON data."""

    def generate(self, data: Any) -> Dict[str, Any]:
        """Generates a JSON Schema dictionary for the given data."""
        schema: Dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#"
        }
        schema.update(self._infer_type(data))
        return schema

    def _infer_type(self, val: Any) -> Dict[str, Any]:
        if val is None:
            return {"type": "null"}
        elif isinstance(val, bool):
            return {"type": "boolean"}
        elif isinstance(val, int):
            return {"type": "integer"}
        elif isinstance(val, float):
            return {"type": "number"}
        elif isinstance(val, str):
            return {"type": "string"}
        elif isinstance(val, dict):
            props = {}
            for k, v in val.items():
                props[k] = self._infer_type(v)
            return {
                "type": "object",
                "properties": props
            }
        elif isinstance(val, list):
            if not val:
                return {"type": "array"}
            item_schema = self._infer_type(val[0])
            return {
                "type": "array",
                "items": item_schema
            }
        else:
            return {}

    def validate(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validates JSON data against a JSON schema."""
        if jsonschema is None:
            return {"success": False, "error": "The 'jsonschema' library is not installed."}
        try:
            jsonschema.validate(instance=data, schema=schema)
            return {"success": True}
        except jsonschema.exceptions.ValidationError as e:
            return {"success": False, "error": e.message, "path": list(e.path)}
        except jsonschema.exceptions.SchemaError as e:
            return {"success": False, "error": f"Invalid schema: {e.message}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def run_json_schema_lab_logic(args) -> bool:
    """CLI logic for json-schema-lab."""
    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        import asyncio
        print("Launching JSON Schema Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json-schema")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
            return True
        else:
            app.run()
            sys.exit(0)

    manager = JsonSchemaManager()
    json_str = ""

    if hasattr(args, "file") and args.file:
        try:
            with open(args.file, "r") as f:
                json_str = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif hasattr(args, "json") and args.json:
        json_str = args.json
    else:
        if not sys.stdin.isatty():
            json_str = sys.stdin.read()
        else:
            print("Error: Please provide JSON via --file, --json, or stdin.", file=sys.stderr)
            return False

    if not json_str.strip():
        print("Error: No JSON data provided.", file=sys.stderr)
        return False

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return False

    if getattr(args, "action", None) == "validate":
        schema_str = ""
        if hasattr(args, "schema_file") and args.schema_file:
            try:
                with open(args.schema_file, "r") as f:
                    schema_str = f.read()
            except Exception as e:
                print(f"Error reading schema file: {e}", file=sys.stderr)
                return False
        elif hasattr(args, "schema") and args.schema:
            schema_str = args.schema
        else:
            print("Error: Please provide JSON schema via --schema-file or --schema.", file=sys.stderr)
            return False

        if not schema_str.strip():
            print("Error: No JSON schema provided.", file=sys.stderr)
            return False

        try:
            schema_data = json.loads(schema_str)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON Schema: {e}", file=sys.stderr)
            return False

        result = manager.validate(data, schema_data)
        if result["success"]:
            print("✅ JSON is valid according to the schema.")
            return True
        else:
            print(f"❌ Validation failed: {result.get('error')}", file=sys.stderr)
            if result.get("path"):
                print(f"   Path: /{'/'.join(map(str, result['path']))}", file=sys.stderr)
            return False

    else:
        schema = manager.generate(data)
        schema_str = json.dumps(schema, indent=2)

        if hasattr(args, "output") and args.output:
            try:
                with open(args.output, "w") as f:
                    f.write(schema_str)
                print(f"✅ Generated JSON Schema saved to {args.output}")
            except Exception as e:
                print(f"Error writing to output file: {e}", file=sys.stderr)
                return False
        else:
            print(schema_str)

        return True
