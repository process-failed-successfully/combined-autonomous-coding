import csv
import io
import sys


class Csv2SqlManager:
    def convert(self, csv_data: str, table_name: str) -> str:
        """
        Converts CSV data into SQL INSERT statements.
        """
        if not csv_data.strip():
            return ""

        f = io.StringIO(csv_data)
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return ""

        if not headers:
            return ""

        # Clean headers
        clean_headers = [h.strip() for h in headers if h.strip()]
        if not clean_headers:
            return ""

        cols_str = ", ".join(clean_headers)
        sql_statements = []

        for row in reader:
            if not row:
                continue

            # Pad row if it has fewer columns than headers
            while len(row) < len(clean_headers):
                row.append("")

            # Truncate row if it has more columns than headers
            row = row[:len(clean_headers)]

            # Escape single quotes
            escaped_values = [v.replace("'", "''") for v in row]
            vals_str = ", ".join(f"'{v}'" for v in escaped_values)

            # Construct SQL
            sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str});"  # nosec B608
            sql_statements.append(sql)

        return "\n".join(sql_statements)


def run_csv2sql_lab_logic(args) -> bool:
    """CLI logic for Csv2Sql Lab."""
    csv_data = ""

    if getattr(args, "text", None):
        csv_data = args.text
    elif getattr(args, "file", None):
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                csv_data = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            return False
    else:
        # Read from stdin
        try:
            csv_data = sys.stdin.read()
        except Exception as e:
            print(f"Error reading from stdin: {e}", file=sys.stderr)
            return False

    table_name = getattr(args, "table", "data_table") or "data_table"

    manager = Csv2SqlManager()
    try:
        sql_output = manager.convert(csv_data, table_name)
        if getattr(args, "output", None):
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(sql_output)
            print(f"✅ SQL statements written to {args.output}")
        else:
            print(sql_output)
        return True
    except Exception as e:
        print(f"Error converting CSV to SQL: {e}", file=sys.stderr)
        return False
