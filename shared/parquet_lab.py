import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json

class ParquetLabManager:
    """
    Manages Parquet operations including reading, writing, and inspecting .parquet files.
    """

    def __init__(self, project_dir: Optional[Path] = None):
        try:
            import pandas as pd
            import pyarrow
        except ImportError:
            raise ImportError("pandas and pyarrow are required. Please install them.")

        self.pd = pd
        self.project_dir = project_dir or Path(".")

    def get_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Returns metadata from a Parquet file."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = self.pd.read_parquet(file_path)
            return {
                "file": str(file_path),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
            }
        except Exception as e:
            raise ValueError(f"Error reading Parquet file {file_path}: {e}")

    def get_schema(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """Returns the schema (column names and types) of a Parquet file."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = self.pd.read_parquet(file_path)
            return {col: str(dtype) for col, dtype in df.dtypes.items()}
        except Exception as e:
            raise ValueError(f"Error reading schema from {file_path}: {e}")

    def read_parquet(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Reads a Parquet file into a list of dictionaries."""
        file_path = Path(file_path).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            df = self.pd.read_parquet(file_path)
            # Convert timestamps to strings for JSON serialization compatibility
            df = df.astype(object).where(self.pd.notnull(df), None)
            return df.to_dict(orient="records")
        except Exception as e:
            raise ValueError(f"Error reading Parquet file {file_path}: {e}")

    def save_parquet(self, data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
        """Writes a list of dictionaries to a Parquet file."""
        if not data:
            # Create empty file with empty DataFrame
            self.pd.DataFrame().to_parquet(file_path)
            return

        try:
            df = self.pd.DataFrame(data)
            df.to_parquet(file_path, index=False)
        except Exception as e:
            raise ValueError(f"Error writing Parquet file {file_path}: {e}")


def run_parquet_lab_logic(args):
    """CLI logic for Parquet Lab."""
    manager = ParquetLabManager(getattr(args, 'project_dir', None))

    if args.action == "info":
        try:
            info = manager.get_info(args.file)
            print(f"--- Parquet File Info: {info['file']} ---")
            print(f"Rows: {info['rows']}")
            print(f"Columns: {info['columns']}")
            print(f"Memory Usage: {info['memory_usage_mb']:.2f} MB")
            print("Columns:")
            for col in info['column_names']:
                print(f"  - {col}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "schema":
        try:
            schema = manager.get_schema(args.file)
            print(f"--- Schema: {args.file} ---")
            for col, dtype in schema.items():
                print(f"{col}: {dtype}")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "read":
        try:
            data = manager.read_parquet(args.file)

            output_format = getattr(args, 'format', 'table')
            output_path_str = getattr(args, 'output', None)

            if output_path_str:
                output_path = Path(output_path_str)
                # Infer format from extension if explicitly "table" (default) but output file given
                if output_format == 'table':
                    if output_path.suffix.lower() == '.json':
                        output_format = 'json'
                    elif output_path.suffix.lower() == '.csv':
                        output_format = 'csv'
                    elif output_path.suffix.lower() == '.parquet':
                        output_format = 'parquet'

                if output_format == "json":
                    with open(output_path, 'w', encoding='utf-8') as f:
                        def json_serial(obj):
                            if hasattr(obj, 'isoformat'):
                                return obj.isoformat()
                            return str(obj)
                        json.dump(data, f, indent=2, default=json_serial)
                    print(f"✅ Saved to {output_path}")
                elif output_format == "csv":
                     manager.pd.DataFrame(data).to_csv(output_path, index=False)
                     print(f"✅ Saved to {output_path}")
                # Parquet to Parquet? redundant but allowed
                elif output_format == "parquet":
                     manager.pd.DataFrame(data).to_parquet(output_path, index=False)
                     print(f"✅ Saved to {output_path}")

            if not output_path_str or output_format == "table":
                if output_format == "table":
                    try:
                        from rich.console import Console
                        from rich.table import Table
                        console = Console()
                        table = Table(show_header=True, header_style="bold magenta")

                        if not data:
                            print("File is empty.")
                            sys.exit(0)

                        headers = list(data[0].keys())
                        for h in headers:
                            table.add_column(h)

                        limit = getattr(args, 'limit', 50)
                        for row in data[:limit]:
                            table.add_row(*[str(row.get(h, "")) for h in headers])

                        console.print(table)
                        if len(data) > limit:
                            console.print(f"[dim]Showing first {limit} of {len(data)} rows.[/dim]")
                    except ImportError:
                        if not data:
                            print("File is empty.")
                            sys.exit(0)
                        print(json.dumps(data[:10], indent=2, default=str)) # Simple fallback

                elif output_format == "json":
                    def json_serial(obj):
                        if hasattr(obj, 'isoformat'):
                            return obj.isoformat()
                        return str(obj)
                    print(json.dumps(data, indent=2, default=json_serial))

        except Exception as e:
            print(f"❌ Error reading Parquet file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "convert":
        # Handled by read + output logic if conversion is from parquet
        if not getattr(args, 'output', None):
             print("Error: --output required for convert action.", file=sys.stderr)
             sys.exit(1)
        # Read is already called above? No, wait.
        # The structure above is `if args.action == "read"`.
        # If action is convert, we can reuse the read logic if the source is parquet.
        # But if the user runs `parquet convert file.parquet --output file.csv`,
        # we can just invoke the read logic which handles output conversion.

        # Let's delegate to read logic for simplicity as it already handles output formats.
        args.action = "read"
        return run_parquet_lab_logic(args)

    return True
