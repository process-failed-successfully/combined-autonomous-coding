import sys
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from rich.console import Console
from rich.table import Table


class SqlLabManager:
    """
    Manages direct SQL execution and schema inspection.
    """
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        try:
            self.engine = create_engine(connection_string)
            self.console = Console()
        except Exception as e:
            print(f"Error creating engine: {e}", file=sys.stderr)
            self.engine = None

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Executes a SQL query and returns results.
        """
        if not self.engine:
            return {"success": False, "error": "No database connection."}

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))

                if result.returns_rows:
                    columns = list(result.keys())
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    return {
                        "success": True,
                        "columns": columns,
                        "rows": rows,
                        "rowcount": len(rows)
                    }
                else:
                    conn.commit()
                    return {
                        "success": True,
                        "rowcount": result.rowcount,
                        "message": "Query executed successfully."
                    }
        except SQLAlchemyError as e:
            return {"success": False, "error": str(e)}

    def list_tables(self) -> List[str]:
        """
        Lists tables in the database.
        """
        if not self.engine:
            return []
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except SQLAlchemyError as e:
            print(f"Error listing tables: {e}", file=sys.stderr)
            return []

    def get_schema(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Gets schema for a specific table or all tables.
        """
        if not self.engine:
            return {}

        try:
            inspector = inspect(self.engine)
            tables = [table_name] if table_name else inspector.get_table_names()
            schema = {}

            for table in tables:
                columns = inspector.get_columns(table)
                schema[table] = [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "default": str(col["default"]) if col["default"] else None
                    }
                    for col in columns
                ]
            return schema
        except SQLAlchemyError as e:
            print(f"Error getting schema: {e}", file=sys.stderr)
            return {}

    def export_query(self, query: str, format: str, output_file: str) -> bool:
        """
        Exports query results to a file.
        """
        result = self.execute_query(query)
        if not result["success"]:
            print(f"Error executing query: {result['error']}", file=sys.stderr)
            return False

        if "rows" not in result:
            print("Query returned no rows to export.", file=sys.stderr)
            return False

        rows = result["rows"]
        columns = result["columns"]

        try:
            if format.lower() == "csv":
                with open(output_file, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=columns)
                    writer.writeheader()
                    writer.writerows(rows)
            elif format.lower() == "json":
                with open(output_file, "w") as f:
                    json.dump(rows, f, indent=2, default=str)
            else:
                print(f"Unknown format: {format}", file=sys.stderr)
                return False

            print(f"Exported {len(rows)} rows to {output_file}")
            return True
        except IOError as e:
            print(f"Error writing file: {e}", file=sys.stderr)
            return False


def detect_connection_string(project_dir: Path) -> str:
    """
    Detects the database connection string for the project.
    Prioritizes DATABASE_URL env var, then searches for local SQLite files.
    """
    conn_str = os.environ.get("DATABASE_URL")
    if conn_str:
        return conn_str

    # Check for local .db or .sqlite files
    # Sort to prioritize certain names? Or just take first.
    try:
        files = [f for f in os.listdir(project_dir) if f.endswith(".db") or f.endswith(".sqlite")]
        if files:
            # If multiple, prefer agent_lab.db if it exists, else the first one
            if "agent_lab.db" in files:
                return f"sqlite:///{project_dir}/agent_lab.db"
            return f"sqlite:///{project_dir}/{files[0]}"
    except OSError:
        pass

    # Default fallback
    return f"sqlite:///{project_dir}/agent_lab.db"


def run_sql_lab_logic(args):
    """
    CLI entry point for SQL Lab.
    """
    # Determine connection string
    conn_str = args.url
    if not conn_str:
        conn_str = detect_connection_string(Path("."))
        print(f"Using database: {conn_str}")

    manager = SqlLabManager(conn_str)

    if args.action == "run":
        if not args.query:
            print("Error: --query is required.", file=sys.stderr)
            sys.exit(1)

        result = manager.execute_query(args.query)
        if result["success"]:
            if "rows" in result:
                table = Table(show_header=True, header_style="bold magenta")
                for col in result["columns"]:
                    table.add_column(col)

                for row in result["rows"]:
                    table.add_row(*[str(row[c]) for c in result["columns"]])

                manager.console.print(table)
                print(f"\n({result['rowcount']} rows)")
            else:
                print(f"✅ {result['message']} (Rows affected: {result.get('rowcount', 0)})")
        else:
            print(f"❌ Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "list":
        tables = manager.list_tables()
        if tables:
            print("--- Tables ---")
            for t in tables:
                print(f"  - {t}")
        else:
            print("No tables found.")

    elif args.action == "schema":
        schema = manager.get_schema(args.table)
        if schema:
            for table_name, columns in schema.items():
                print(f"\nTable: {table_name}")
                schema_table = Table(show_header=True)
                schema_table.add_column("Column")
                schema_table.add_column("Type")
                schema_table.add_column("Nullable")
                schema_table.add_column("Default")

                for col in columns:
                    schema_table.add_row(
                        col["name"],
                        col["type"],
                        str(col["nullable"]),
                        str(col["default"])
                    )
                manager.console.print(schema_table)
        else:
            print("Schema information not found.")

    elif args.action == "export":
        if not args.query or not args.output:
            print("Error: --query and --output are required.", file=sys.stderr)
            sys.exit(1)

        success = manager.export_query(args.query, args.format, args.output)
        sys.exit(0 if success else 1)
