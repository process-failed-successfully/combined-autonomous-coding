import sys
import json
import argparse
from typing import Dict, Any

class Json2SqlManager:
    """Manages conversion from JSON format to SQL INSERT statements."""

    def __init__(self):
        pass

    def _escape_sql_value(self, value: Any) -> str:
        """Escapes a value for a SQL string."""
        if value is None:
            return "NULL"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            # It's a string or dict/list that we stringify
            if isinstance(value, (dict, list)):
                string_val = json.dumps(value)
            else:
                string_val = str(value)
            # Escape single quotes
            escaped_val = string_val.replace("'", "''")
            return f"'{escaped_val}'"

    def convert(self, json_str: str, table_name: str) -> Dict[str, Any]:
        """Converts JSON data to SQL INSERT statements."""
        if not json_str or not json_str.strip():
            return {"success": False, "error": "Empty input."}

        if not table_name or not table_name.strip():
            return {"success": False, "error": "Table name is required."}

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}

        # Normalization: ensure data is a list of dicts
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return {"success": False, "error": "JSON data must be an object or a list of objects."}

        if not data:
            return {"success": False, "error": "JSON list is empty."}

        statements = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                return {"success": False, "error": f"Item at index {index} is not an object."}

            if not item:
                continue

            columns = list(item.keys())
            values = [self._escape_sql_value(item[c]) for c in columns]

            cols_str = ", ".join(columns)
            vals_str = ", ".join(values)

            stmt = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str});"  # nosec B608
            statements.append(stmt)

        if not statements:
            return {"success": False, "error": "No valid data to convert."}

        return {"success": True, "sql": "\n".join(statements)}


def run_json2sql_lab_logic(args) -> bool:
    """CLI Entry point for Json2Sql Lab."""
    # Action 'tui' should have been caught in main.py, but just in case
    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        try:
            from shared.tui import AgentTUI
            import asyncio
            from pathlib import Path
            print("Launching Json2Sql Lab TUI...")
            app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-json2sql")
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass
            if loop and loop.is_running():
                asyncio.ensure_future(app.run_async())
            else:
                app.run()
            return True
        except ImportError as e:
            print(f"Error launching TUI: {e}", file=sys.stderr)
            return False

    manager = Json2SqlManager()

    # Process text or file
    json_content = ""
    if getattr(args, "text", None):
        json_content = args.text
    elif getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                json_content = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    else:
        # Check stdin
        if not sys.stdin.isatty():
            json_content = sys.stdin.read()
        else:
            print("Error: Please provide --file, --text, or pipe JSON via stdin.", file=sys.stderr)
            return False

    table_name = getattr(args, "table", "mytable")
    if not table_name:
        table_name = "mytable"

    result = manager.convert(json_content, table_name)
    if not result["success"]:
        print(f"Error converting JSON to SQL: {result['error']}", file=sys.stderr)
        return False

    output_sql = result["sql"]

    output_file = getattr(args, "output", None)
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_sql)
            print(f"Successfully wrote SQL to {output_file}")
        except Exception as e:
            print(f"Error writing to {output_file}: {e}", file=sys.stderr)
            return False
    else:
        print(output_sql)

    return True
