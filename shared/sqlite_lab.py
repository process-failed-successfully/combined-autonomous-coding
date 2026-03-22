import sqlite3
import csv
import sys
import io
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path


class SqliteLabManager:
    """
    Manages SQLite database connections and queries.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establishes connection to the database."""
        if self._conn is None:
            # check if file exists unless it's :memory:
            if self.db_path != ":memory:":
                p = Path(self.db_path)
                if not p.exists() and not p.parent.exists():
                    raise FileNotFoundError(f"Database directory does not exist: {p.parent}")
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """Closes the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute_query(self, query: str, params: tuple = ()) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Executes a SQL query and returns column names and rows.
        For non-SELECT queries, returns affected row count in a simulated format.
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if cursor.description:
                columns = [col[0] for col in cursor.description]
                rows = [dict(row) for row in cursor.fetchall()]
                return columns, rows
            else:
                conn.commit()
                # For INSERT/UPDATE/DELETE, return a status
                return ["Status", "Rows Affected"], [{"Status": "Success", "Rows Affected": cursor.rowcount}]
        except sqlite3.Error as e:
            raise ValueError(f"SQLite Error: {e}")

    def get_tables(self) -> List[str]:
        """Lists all tables and views in the database."""
        query = "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        _, rows = self.execute_query(query)
        return [row["name"] for row in rows]

    def get_schema(self, table_name: Optional[str] = None) -> str:
        """Returns the schema for a specific table or all tables."""
        if table_name:
            query = "SELECT sql FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?;"
            _, rows = self.execute_query(query, (table_name,))
        else:
            query = "SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY name;"
            _, rows = self.execute_query(query)

        if not rows:
            return "No schema found."

        schema_lines = []
        for row in rows:
            if row.get("sql"):
                schema_lines.append(row["sql"] + ";")
            else:
                name = row.get("name", table_name)
                schema_lines.append(f"-- Schema not available for {name}")

        return "\n\n".join(schema_lines)

    def export_csv(self, columns: List[str], rows: List[Dict[str, Any]]) -> str:
        """Exports the result as a CSV string."""
        if not columns:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()


def run_sqlite_lab_logic(args) -> bool:
    """CLI logic for SQLite Lab."""
    manager = SqliteLabManager(args.db)

    try:
        if args.action == "query":
            columns, rows = manager.execute_query(args.query)
            if not columns and not rows:
                print("Query executed successfully. No data returned.")
            else:
                if args.format == "csv":
                    print(manager.export_csv(columns, rows))
                else:
                    import json
                    print(json.dumps(rows, indent=2))

        elif args.action == "tables":
            tables = manager.get_tables()
            if tables:
                print("Tables:")
                for t in tables:
                    print(f"  - {t}")
            else:
                print("No tables found.")

        elif args.action == "schema":
            schema = manager.get_schema(args.table)
            print(schema)

        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    finally:
        manager.close()
