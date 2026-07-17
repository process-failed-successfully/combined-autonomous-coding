import sys
import json
import csv
import io
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None


class PostgresLabManager:
    """
    Manages PostgreSQL database connections and queries.
    """

    def __init__(self, uri: str = "postgresql://postgres:postgres@localhost:5432/postgres"):
        self.uri = uri
        self._conn = None

    def connect(self):
        """Establishes connection to the database."""
        if psycopg2 is None:
            raise ImportError("psycopg2 is not installed. Please run 'pip install psycopg2-binary'.")
        if self._conn is None:
            self._conn = psycopg2.connect(self.uri)
            self._conn.autocommit = True
        return self._conn

    def close(self):
        """Closes the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute_query(self, query: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Executes a query and returns column names and rows.
        """
        conn = self.connect()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    # Convert to standard dict to avoid serialization issues
                    rows = [dict(row) for row in rows]
                    return columns, rows
                else:
                    return ["Status", "Rows Affected"], [{"Status": "Success", "Rows Affected": cursor.rowcount}]
        except Exception as e:
            raise ValueError(f"PostgreSQL Error: {e}")

    def get_tables(self) -> List[str]:
        """Gets a list of all tables in the current database."""
        query = """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';
        """
        try:
            _, rows = self.execute_query(query)
            return [row["tablename"] for row in rows]
        except Exception as e:
            print(f"Error fetching tables: {e}", file=sys.stderr)
            return []

    def get_schema(self, table_name: Optional[str] = None) -> List[str]:
        """Gets schema definitions for tables."""
        schemas = []
        tables = [table_name] if table_name else self.get_tables()

        for t in tables:
            query = f"""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{t}';
            """
            try:
                _, rows = self.execute_query(query)
                cols_def = []
                for row in rows:
                    col_def = f"{row['column_name']} {row['data_type']}"
                    if row['character_maximum_length']:
                        col_def += f"({row['character_maximum_length']})"
                    if row['is_nullable'] == 'NO':
                        col_def += " NOT NULL"
                    cols_def.append(col_def)

                schema_str = f"CREATE TABLE {t} (\n  " + ",\n  ".join(cols_def) + "\n);"
                schemas.append(schema_str)
            except Exception as e:
                schemas.append(f"Error fetching schema for {t}: {e}")

        return schemas

    def export_csv(self, columns: List[str], rows: List[Dict[str, Any]]) -> str:
        """Exports query results to a CSV string."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()


def run_postgres_lab_logic(args) -> bool:
    """Handles the CLI logic for Postgres Lab."""
    if psycopg2 is None:
        print("Error: 'psycopg2' is not installed. Please run 'pip install psycopg2-binary'.", file=sys.stderr)
        return False

    uri = getattr(args, 'uri', "postgresql://postgres:postgres@localhost:5432/postgres")
    manager = PostgresLabManager(uri=uri)

    try:
        manager.connect()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}", file=sys.stderr)
        return False

    try:
        if args.action == "query":
            try:
                columns, rows = manager.execute_query(args.query)
                if args.format == "csv":
                    print(manager.export_csv(columns, rows))
                else:
                    print(json.dumps(rows, indent=2, default=str))
            except Exception as e:
                print(f"Error executing query: {e}", file=sys.stderr)
                return False

        elif args.action == "tables":
            tables = manager.get_tables()
            for t in tables:
                print(t)

        elif args.action == "schema":
            schemas = manager.get_schema(getattr(args, 'table', None))
            for s in schemas:
                print(s)
                print("-" * 40)

        return True

    finally:
        manager.close()
