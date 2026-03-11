import csv
import sys
import argparse
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

class CsvLabManager:
    """
    Manages CSV operations including reading, writing, filtering, sorting, and analyzing.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")

    def load_csv(self, path: Union[str, Path]) -> List[Dict[str, str]]:
        """Reads a CSV file into a list of dictionaries."""
        path = Path(path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8', newline='') as f:
                # Check if empty
                f.seek(0, 2)
                if f.tell() == 0:
                    return []
                f.seek(0)

                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            raise ValueError(f"Error reading CSV {path}: {e}")

    def save_csv(self, data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
        """Writes a list of dictionaries to a CSV file."""
        if not data:
            # Create empty file
            Path(path).write_text("", encoding="utf-8")
            return

        keys = data[0].keys()

        try:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            raise ValueError(f"Error writing CSV {path}: {e}")

    def get_headers(self, data: List[Dict[str, Any]]) -> List[str]:
        """Returns the list of column names."""
        if not data:
            return []
        return list(data[0].keys())

    def get_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates basic statistics for the CSV data."""
        if not data:
            return {"rows": 0, "columns": 0, "empty_cells": 0}

        headers = self.get_headers(data)
        row_count = len(data)
        col_count = len(headers)
        empty_cells = sum(1 for row in data for k in headers if not row.get(k))

        return {
            "rows": row_count,
            "columns": col_count,
            "empty_cells": empty_cells
        }

    def filter_data(self, data: List[Dict[str, Any]], column: str, value: str, operator: str = "eq") -> List[Dict[str, Any]]:
        """
        Filters data based on a column value and operator.
        Operators: eq (=), neq (!=), gt (>), lt (<), gte (>=), lte (<=), contains.
        """
        if not data:
            return []

        if column not in data[0]:
            raise ValueError(f"Column '{column}' not found.")

        filtered = []
        for row in data:
            cell = row.get(column, "")

            # Try numeric conversion for comparison operators
            cell_val = cell
            comp_val = value
            is_numeric = False

            if operator in ["gt", "lt", "gte", "lte"]:
                try:
                    cell_val = float(cell)
                    comp_val = float(value)
                    is_numeric = True
                except ValueError:
                    pass # Fallback to string comparison

            match = False
            if operator == "eq":
                match = (cell == value)
            elif operator == "neq":
                match = (cell != value)
            elif operator == "contains":
                match = (value.lower() in cell.lower())
            elif operator == "gt":
                match = (cell_val > comp_val)
            elif operator == "lt":
                match = (cell_val < comp_val)
            elif operator == "gte":
                match = (cell_val >= comp_val)
            elif operator == "lte":
                match = (cell_val <= comp_val)
            else:
                raise ValueError(f"Unknown operator: {operator}")

            if match:
                filtered.append(row)

        return filtered

    def sort_data(self, data: List[Dict[str, Any]], column: str, reverse: bool = False, numeric: bool = False) -> List[Dict[str, Any]]:
        """Sorts data by a specific column."""
        if not data:
            return []

        if column not in data[0]:
            raise ValueError(f"Column '{column}' not found.")

        def key_func(row):
            val = row.get(column, "")
            if numeric:
                try:
                    return float(val)
                except ValueError:
                    return float('-inf') # Push invalid to bottom (or top)
            return val

        return sorted(data, key=key_func, reverse=reverse)

    def select_columns(self, data: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
        """Returns data with only specified columns."""
        if not data:
            return []

        # Validate columns
        available = set(data[0].keys())
        missing = [c for c in columns if c not in available]
        if missing:
            raise ValueError(f"Columns not found: {', '.join(missing)}")

        return [{k: row[k] for k in columns} for row in data]

    def query_sql(self, data: List[Dict[str, Any]], query: str, table_name: str = "data") -> List[Dict[str, Any]]:
        """
        Executes a SQL query on the CSV data using an in-memory SQLite database.
        Automatically infers column types to support numeric operations.
        """
        if not data:
            return []

        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row

        headers = self.get_headers(data)

        # 1. Infer Types
        types = {}
        for h in headers:
            can_be_int = True
            can_be_float = True

            # Check up to first 100 rows to guess type
            for row in data[:100]:
                val = row.get(h)
                if not val: # skip empty string or None
                    continue
                if can_be_int:
                    try:
                        int(val)
                    except ValueError:
                        can_be_int = False
                if can_be_float:
                    try:
                        float(val)
                    except ValueError:
                        can_be_float = False

                if not can_be_int and not can_be_float:
                    break

            if can_be_int:
                types[h] = "INTEGER"
            elif can_be_float:
                types[h] = "REAL"
            else:
                types[h] = "TEXT"

        # 2. Create Table
        # Quote column names to handle spaces or reserved words
        cols = [f'"{h}" {types[h]}' for h in headers]
        create_stmt = f"CREATE TABLE {table_name} ({', '.join(cols)})"
        conn.execute(create_stmt)  # nosec B608

        # 3. Insert Data
        placeholders = ", ".join(["?"] * len(headers))
        insert_stmt = f"INSERT INTO {table_name} ({', '.join(['\"'+h+'\"' for h in headers])}) VALUES ({placeholders})"  # nosec B608

        # Prepare rows for insertion (convert types so SQLite stores them correctly)
        insert_data = []
        for row in data:
            r = []
            for h in headers:
                val = row.get(h)
                if not val:
                    r.append(None)
                elif types[h] == "INTEGER":
                    try:
                        r.append(int(val))
                    except ValueError:
                        r.append(None)
                elif types[h] == "REAL":
                    try:
                        r.append(float(val))
                    except ValueError:
                        r.append(None)
                else:
                    r.append(val)
            insert_data.append(r)

        conn.executemany(insert_stmt, insert_data)

        # 4. Execute Query
        try:
            cursor = conn.execute(query)
            result = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            conn.close()
            raise ValueError(f"SQL Error: {e}")

        conn.close()
        return result


def run_csv_lab_logic(args):
    """CLI logic for CSV Lab."""
    manager = CsvLabManager(args.project_dir)

    if args.action == "tui":
        from shared.tui import AgentTUI
        print("Launching CSV Lab TUI...")
        app = AgentTUI(project_dir=manager.project_dir, start_tab="tab-csv")
        app.run()
        sys.exit(0)

    # Load input
    if args.file:
        try:
            data = manager.load_csv(args.file)
        except Exception as e:
            print(f"❌ Error loading CSV: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Try reading from stdin if no file provided
        if not sys.stdin.isatty():
            try:
                content = sys.stdin.read()
                reader = csv.DictReader(content.splitlines())
                data = list(reader)
            except Exception as e:
                print(f"❌ Error reading from stdin: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("❌ Error: Input file required (or pipe to stdin).", file=sys.stderr)
            sys.exit(1)

    if args.action == "read":
        # Pretty print using Rich if available, else simple table
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(show_header=True, header_style="bold magenta")

            headers = manager.get_headers(data)
            for h in headers:
                table.add_column(h)

            limit = getattr(args, 'limit', 50)
            for row in data[:limit]:
                table.add_row(*[str(row.get(h, "")) for h in headers])

            console.print(table)
            if len(data) > limit:
                console.print(f"[dim]Showing first {limit} of {len(data)} rows.[/dim]")

        except ImportError:
            # Fallback
            headers = manager.get_headers(data)
            print(",".join(headers))
            for row in data:
                print(",".join(str(row.get(h, "")) for h in headers))

    elif args.action == "headers":
        headers = manager.get_headers(data)
        for h in headers:
            print(h)

    elif args.action == "stats":
        stats = manager.get_stats(data)
        print("--- CSV Statistics ---")
        print(f"Rows:        {stats['rows']}")
        print(f"Columns:     {stats['columns']}")
        print(f"Empty Cells: {stats['empty_cells']}")

    elif args.action == "filter":
        try:
            result = manager.filter_data(data, args.column, args.value, args.operator)
            if args.output:
                manager.save_csv(result, args.output)
                print(f"✅ Filtered data saved to {args.output}")
            else:
                # Output as CSV to stdout
                if result:
                    writer = csv.DictWriter(sys.stdout, fieldnames=result[0].keys())
                    writer.writeheader()
                    writer.writerows(result)
        except ValueError as e:
            print(f"❌ Filter error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "sort":
        try:
            result = manager.sort_data(data, args.column, args.reverse, args.numeric)
            if args.output:
                manager.save_csv(result, args.output)
                print(f"✅ Sorted data saved to {args.output}")
            else:
                if result:
                    writer = csv.DictWriter(sys.stdout, fieldnames=result[0].keys())
                    writer.writeheader()
                    writer.writerows(result)
        except ValueError as e:
            print(f"❌ Sort error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "select":
        try:
            cols = [c.strip() for c in args.columns.split(",")]
            result = manager.select_columns(data, cols)
            if args.output:
                manager.save_csv(result, args.output)
                print(f"✅ Selected data saved to {args.output}")
            else:
                if result:
                    writer = csv.DictWriter(sys.stdout, fieldnames=result[0].keys())
                    writer.writeheader()
                    writer.writerows(result)
        except ValueError as e:
            print(f"❌ Select error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "query":
        try:
            result = manager.query_sql(data, args.query)
            if args.output:
                manager.save_csv(result, args.output)
                print(f"✅ Query results saved to {args.output}")
            else:
                if result:
                    try:
                        from rich.console import Console
                        from rich.table import Table
                        console = Console()
                        table = Table(show_header=True, header_style="bold magenta")

                        headers = list(result[0].keys())
                        for h in headers:
                            table.add_column(h)

                        limit = getattr(args, 'limit', 50)
                        for row in result[:limit]:
                            table.add_row(*[str(row.get(h, "")) for h in headers])

                        console.print(table)
                        if len(result) > limit:
                            console.print(f"[dim]Showing first {limit} of {len(result)} rows.[/dim]")
                    except ImportError:
                        writer = csv.DictWriter(sys.stdout, fieldnames=result[0].keys())
                        writer.writeheader()
                        writer.writerows(result)
                else:
                    print("No results returned.")
        except ValueError as e:
            print(f"❌ Query error: {e}", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)
