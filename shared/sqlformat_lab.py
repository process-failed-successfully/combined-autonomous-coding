import sys
import sqlparse
from pathlib import Path


class SqlFormatManager:
    """Manages SQL parsing and formatting."""

    def __init__(self):
        pass

    def format_sql(self, sql_content: str, reindent: bool = True,
                   keyword_case: str = "upper", identifier_case: str = "lower") -> str:
        """Formats the given SQL string."""
        return sqlparse.format(
            sql_content,
            reindent=reindent,
            keyword_case=keyword_case,
            identifier_case=identifier_case
        )

    def process(self, input_text: str = None, file_path: str = None,
                output_path: str = None, reindent: bool = True,
                keyword_case: str = "upper", identifier_case: str = "lower") -> bool:
        """Reads input, formats it, and writes to output or prints."""
        if not input_text and not file_path:
            print("Error: Must provide either input_text or file_path.", file=sys.stderr)
            return False

        if file_path:
            path = Path(file_path)
            if not path.is_file():
                print(f"Error: File '{file_path}' not found.", file=sys.stderr)
                return False
            try:
                input_text = path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
                return False

        formatted_sql = self.format_sql(
            input_text,
            reindent=reindent,
            keyword_case=keyword_case,
            identifier_case=identifier_case
        )

        if output_path:
            try:
                out_path = Path(output_path)
                out_path.write_text(formatted_sql, encoding="utf-8")
                print(f"✅ Formatted SQL saved to {output_path}")
            except Exception as e:
                print(f"Error writing to file '{output_path}': {e}", file=sys.stderr)
                return False
        else:
            print(formatted_sql)

        return True


def run_sqlformat_lab_logic(args):
    """CLI logic for SQL Format Lab."""
    manager = SqlFormatManager()

    input_text = getattr(args, "text", None)
    file_path = getattr(args, "file", None)
    output_path = getattr(args, "output", None)
    reindent = not getattr(args, "no_reindent", False)
    keyword_case = getattr(args, "keyword_case", "upper")
    identifier_case = getattr(args, "identifier_case", "lower")

    if not input_text and not file_path:
        print("Error: You must provide either --text or --file.", file=sys.stderr)
        return False

    return manager.process(
        input_text=input_text,
        file_path=file_path,
        output_path=output_path,
        reindent=reindent,
        keyword_case=keyword_case,
        identifier_case=identifier_case
    )
