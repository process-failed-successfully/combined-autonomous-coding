import json
import sys
import argparse
from typing import Any, Dict, List, Union


class Json2SqlManager:
    """Manages the conversion of JSON data to SQL INSERT statements."""

    def convert(self, json_data: Union[str, List[Dict[str, Any]], Dict[str, Any]], table_name: str) -> str:
        """Converts JSON data into SQL INSERT statements."""

        # Parse if string
        if isinstance(json_data, str):
            if not json_data.strip():
                return ""
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e}")
        else:
            data = json_data

        if not data:
            return ""

        # Normalize to list of objects
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise ValueError("JSON data must be an object or an array of objects.")

        if len(data) == 0:
            return ""

        sql_statements = []

        for row in data:
            if not isinstance(row, dict):
                continue

            keys = []
            values = []

            for k, v in row.items():
                keys.append(k)

                # Flatten complex objects/arrays to strings
                if isinstance(v, (dict, list)):
                    v_str = json.dumps(v)
                elif v is None:
                    v_str = "NULL"
                elif isinstance(v, bool):
                    v_str = "TRUE" if v else "FALSE"
                else:
                    v_str = str(v)

                # Format value for SQL
                if v is None:
                    values.append("NULL")
                elif isinstance(v, bool):
                    values.append("TRUE" if v else "FALSE")
                else:
                    # Escape single quotes
                    escaped_v = v_str.replace("'", "''")
                    values.append(f"'{escaped_v}'")

            if not keys:
                continue

            cols_str = ", ".join(keys)
            vals_str = ", ".join(values)

            # Construct SQL
            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str});"  # nosec B608
            sql_statements.append(sql)

        return "\n".join(sql_statements)


def run_json2sql_lab_logic(args: argparse.Namespace) -> bool:
    """CLI logic for Json2Sql Lab."""

    if getattr(args, "tui", False) or getattr(args, "action", None) == "tui":
        from shared.tui import AgentTUI
        print("Launching JSON to SQL Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-json2sql")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
        return True

    json_data = ""

    if getattr(args, "text", None):
        json_data = args.text
    elif getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                json_data = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    else:
        # Read from stdin
        try:
            if not sys.stdin.isatty():
                json_data = sys.stdin.read().strip()
            else:
                print("Error: No input provided. Provide --file, --text, or pass JSON via stdin.", file=sys.stderr)
                return False
        except Exception as e:
            print(f"Error reading from stdin: {e}", file=sys.stderr)
            return False

    if not json_data.strip():
        print("Error: Input data is empty.", file=sys.stderr)
        return False

    table_name = getattr(args, "table", "data_table") or "data_table"

    manager = Json2SqlManager()
    try:
        sql_output = manager.convert(json_data, table_name)
        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(sql_output)
            print(f"✅ SQL statements written to {args.output}")
        else:
            print(sql_output)
        return True
    except Exception as e:
        print(f"Error converting JSON to SQL: {e}", file=sys.stderr)
        return False
