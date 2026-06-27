import duckdb
import csv
import sys
import io
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

class DuckDBLabManager:
    """
    Manages DuckDB database connections and queries.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establishes connection to the database."""
        if self._conn is None:
            if self.db_path != ":memory:":
                p = Path(self.db_path)
                if not p.exists() and not p.parent.exists():
                    raise FileNotFoundError(f"Database directory does not exist: {p.parent}")
            self._conn = duckdb.connect(self.db_path)
        return self._conn

    def close(self):
        """Closes the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute_query(self, query: str, params: tuple = ()) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Executes a SQL query and returns column names and rows.
        """

        conn = self.connect()
        try:
            conn.execute(query, params)
            description = conn.description
            if description:
                columns = [col[0] for col in description]
                fetched = conn.fetchall()
                if not fetched and len(columns) == 1 and columns[0] == 'Count':
                    return ["Status", "Rows Affected"], [{"Status": "Success", "Rows Affected": 0}]
                if fetched and len(columns) == 1 and columns[0] == 'Count':
                    return ["Status", "Rows Affected"], [{"Status": "Success", "Rows Affected": fetched[0][0]}]

                rows = []
                for row in fetched:
                    row_dict = dict(zip(columns, row))
                    rows.append(row_dict)
                return columns, rows
            else:
                return ["Status", "Rows Affected"], [{"Status": "Success", "Rows Affected": 0}]
        except duckdb.Error as e:
            raise ValueError(f"DuckDB Error: {e}")
        except Exception as e:
            raise ValueError(f"Error: {e}")

    def get_tables(self) -> List[str]:
        """Lists all tables and views in the database."""
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name;"
        _, rows = self.execute_query(query)
        return [row["table_name"] for row in rows]

    def get_schema(self, table_name: Optional[str] = None) -> str:
        """Returns the schema for a specific table or all tables."""
        conn = self.connect()
        if table_name:
            query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ?;"
            columns, rows = self.execute_query(query, (table_name,))
        else:
            query = "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='main' ORDER BY table_name, ordinal_position;"
            columns, rows = self.execute_query(query)

        if not rows:
            return "No schema found."

        schema_lines = []
        if table_name:
            schema_lines.append(f"Table: {table_name}")
            for row in rows:
                schema_lines.append(f"  {row['column_name']}: {row['data_type']}")
        else:
            current_table = None
            for row in rows:
                if row['table_name'] != current_table:
                    current_table = row['table_name']
                    schema_lines.append(f"\nTable: {current_table}")
                schema_lines.append(f"  {row['column_name']}: {row['data_type']}")

        return "\n".join(schema_lines).strip()

    def export_csv(self, columns: List[str], rows: List[Dict[str, Any]]) -> str:
        """Exports the result as a CSV string."""
        if not columns:
            return ""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()


def run_duckdb_lab_logic(args) -> bool:
    """CLI logic for DuckDB Lab."""
    manager = DuckDBLabManager(args.db)

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
                    print(json.dumps(rows, indent=2, default=str)) # default=str to handle dates/UUIDs if any

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
