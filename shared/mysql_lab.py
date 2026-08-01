import sys
import json
import csv
import io
from typing import List, Dict, Any, Tuple, Optional

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    pymysql = None


class MysqlLabManager:
    """
    Manages MySQL database connections and queries.
    """

    def __init__(self, uri: str = "mysql://root:root@localhost:3306/mysql"):
        self.uri = uri
        self._conn = None

    def _parse_uri(self, uri: str) -> Dict[str, Any]:
        """Parses a MySQL URI string into connection arguments."""
        # Simple parser for mysql://user:password@host:port/database
        import re
        pattern = r"mysql://(?:(?P<user>[^:]+):?(?P<password>[^@]*)@)?(?P<host>[^:/]+)(?::(?P<port>\d+))?(?:/(?P<database>.*))?"
        match = re.match(pattern, uri)
        if not match:
            raise ValueError("Invalid MySQL URI format. Expected mysql://user:password@host:port/database")

        db_args = match.groupdict()
        if db_args['port']:
            db_args['port'] = int(db_args['port'])
        else:
            db_args['port'] = 3306

        if not db_args['host']:
            db_args['host'] = 'localhost'

        # Remove None values
        return {k: v for k, v in db_args.items() if v is not None}

    def connect(self):
        """Establishes connection to the database."""
        if pymysql is None:
            raise ImportError("pymysql is not installed. Please run 'pip install pymysql'.")
        if self._conn is None:
            kwargs = self._parse_uri(self.uri)
            kwargs['cursorclass'] = pymysql.cursors.DictCursor
            self._conn = pymysql.connect(**kwargs)
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
            with conn.cursor() as cursor:
                cursor.execute(query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    # Convert to standard dict to avoid serialization issues
                    rows = [dict(row) for row in rows]
                    return columns, rows
                else:
                    conn.commit()
                    return ["Status", "Rows Affected"], [{"Status": "Success", "Rows Affected": cursor.rowcount}]
        except Exception as e:
            raise ValueError(f"MySQL Error: {e}")

    def get_tables(self) -> List[str]:
        """Gets a list of all tables in the current database."""
        query = "SHOW TABLES"
        try:
            columns, rows = self.execute_query(query)
            if not columns:
                return []
            col_name = columns[0]
            return [row[col_name] for row in rows]
        except Exception as e:
            print(f"Error fetching tables: {e}", file=sys.stderr)
            return []

    def get_schema(self, table_name: Optional[str] = None) -> List[str]:
        """Gets schema definitions for tables."""
        schemas = []
        tables = [table_name] if table_name else self.get_tables()

        for t in tables:
            query = f"SHOW CREATE TABLE `{t}`"  # nosec B608
            try:
                _, rows = self.execute_query(query)
                if rows:
                    if 'Create Table' in rows[0]:
                        schemas.append(rows[0]['Create Table'] + ";")
                    elif 'Create View' in rows[0]:
                        schemas.append(rows[0]['Create View'] + ";")
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


def run_mysql_lab_logic(args) -> bool:
    """Handles the CLI logic for MySQL Lab."""
    if pymysql is None:
        print("Error: 'pymysql' is not installed. Please run 'pip install pymysql'.", file=sys.stderr)
        return False

    uri = getattr(args, 'uri', None) or "mysql://root:root@localhost:3306/mysql"
    manager = MysqlLabManager(uri=uri)

    try:
        manager.connect()
    except Exception as e:
        print(f"Error connecting to MySQL: {e}", file=sys.stderr)
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
