"""
CSV to SQL Lab
==============

Utilities for converting CSV strings or files into SQL INSERT statements.
"""

import sys
import argparse
import csv
import io


class Csv2SqlManager:
    """Manages conversion between CSV format and SQL INSERT statements."""

    def _infer_value(self, val: str) -> str:
        """Infers the SQL value type for a string and formats it."""
        val = val.strip()
        if not val or val.lower() in ("null", "none"):
            return "NULL"

        # Check if integer
        if val.lstrip('-+').isdigit():
            return val

        # Check if float
        try:
            float(val)
            return val
        except ValueError:
            pass

        # Check if boolean
        if val.lower() in ("true", "false", "t", "f"):
            return "TRUE" if val.lower() in ("true", "t") else "FALSE"

        # String - escape single quotes
        escaped_val = val.replace("'", "''")
        return f"'{escaped_val}'"

    def convert_to_sql(self, csv_data: str, table_name: str = "my_table", delimiter: str = ',') -> str:
        """
        Converts a CSV string to SQL INSERT statements.

        Args:
            csv_data: The CSV string content.
            table_name: The name of the SQL table to insert into.
            delimiter: The character used to separate fields.

        Returns:
            A string containing SQL INSERT statements.
        """
        if not csv_data.strip():
            return "-- No data provided."

        f = io.StringIO(csv_data)
        reader = csv.reader(f, delimiter=delimiter)

        try:
            headers = next(reader)
            headers = [h.strip() for h in headers]
        except StopIteration:
            return "-- CSV is empty."

        if not headers:
            return "-- CSV has no headers."

        cols = ", ".join(f'"{h}"' for h in headers)

        sql_statements = []
        for i, row in enumerate(reader, start=2):
            if not any(field.strip() for field in row):
                continue

            # Pad row if it has fewer columns than headers
            while len(row) < len(headers):
                row.append("")

            # Truncate row if it has more columns than headers
            row = row[:len(headers)]

            values = [self._infer_value(val) for val in row]
            vals_str = ", ".join(values)
            stmt = f"INSERT INTO {table_name} ({cols}) VALUES ({vals_str});"  # nosec B608
            sql_statements.append(stmt)

        if not sql_statements:
            return "-- No data rows found."

        return "\n".join(sql_statements)


def run_csv2sql_lab_logic(args: argparse.Namespace) -> bool:
    """CLI handler for CSV to SQL Lab."""
    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        # We handle this case in main.py, but just in case
        return True

    manager = Csv2SqlManager()

    csv_data = ""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                csv_data = f.read()
        except IOError as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        csv_data = args.text
    elif not sys.stdin.isatty():
        try:
            csv_data = sys.stdin.read()
        except Exception as e:
            print(f"Error reading stdin: {e}", file=sys.stderr)
            return False
    else:
        print("Error: No CSV data provided via --text, --file, or stdin.", file=sys.stderr)
        return False

    delimiter = getattr(args, "delimiter", ",")
    table_name = getattr(args, "table", "my_table")

    try:
        sql_output = manager.convert_to_sql(csv_data, table_name=table_name, delimiter=delimiter)

        output_file = getattr(args, "output", None)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(sql_output)
            print(f"✅ Successfully wrote SQL statements to '{output_file}'.")
        else:
            print(sql_output)

        return True
    except Exception as e:
        print(f"Error converting CSV to SQL: {e}", file=sys.stderr)
        return False
