
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

class ParquetLabManager:
    """
    Manages Parquet file operations using pandas and pyarrow.
    """
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir or Path(".")
        self.pd = None
        self.pa = None
        self.pq = None

    def _check_deps(self):
        try:
            import pandas as pd_module
            self.pd = pd_module
        except ImportError:
            raise ImportError("pandas is required for Parquet Lab. Please install it with 'pip install pandas'.")

        try:
            import pyarrow as pa_module
            import pyarrow.parquet as pq_module
            self.pa = pa_module
            self.pq = pq_module
        except ImportError:
            raise ImportError("pyarrow is required for Parquet Lab. Please install it with 'pip install pyarrow'.")

    def read_parquet(self, filepath: Path, limit: Optional[int] = None) -> str:
        """
        Reads a parquet file and returns a string representation of the dataframe.
        """
        self._check_deps()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            if limit:
                 # Use iter_batches to avoid loading the full file if limit is set
                 parquet_file = self.pq.ParquetFile(str(filepath))

                 # Get the first batch with at least 'limit' rows
                 # batch_size=limit ensures we don't read much more than needed (though row group size matters)
                 batches = parquet_file.iter_batches(batch_size=limit)

                 try:
                     first_batch = next(batches)
                     df = first_batch.to_pandas()
                     return df.head(limit).to_string()
                 except StopIteration:
                     # File is empty
                     return "Empty Parquet file."
            else:
                 df = self.pd.read_parquet(filepath)
                 return df.to_string()

        except Exception as e:
            raise RuntimeError(f"Error reading parquet file: {e}")

    def get_schema(self, filepath: Path) -> Dict[str, Any]:
        """
        Returns schema and metadata of the parquet file.
        """
        self._check_deps()
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            parquet_file = self.pq.ParquetFile(str(filepath))
            schema = parquet_file.schema
            metadata = parquet_file.metadata

            info = {
                "num_rows": metadata.num_rows,
                "num_columns": metadata.num_columns,
                "num_row_groups": metadata.num_row_groups,
                "format_version": metadata.format_version,
                "serialized_size": metadata.serialized_size,
                "columns": []
            }

            for i in range(len(schema)):
                col = schema[i]
                info["columns"].append({
                    "name": col.name,
                    "type": str(col.physical_type),
                    "logical_type": str(col.logical_type),
                    "converted_type": str(col.converted_type)
                })

            return info

        except Exception as e:
            raise RuntimeError(f"Error reading schema: {e}")

    def convert(self, input_path: Path, output_path: Path, format: str) -> Path:
        """
        Converts parquet file to CSV or JSON.
        """
        self._check_deps()
        if not input_path.exists():
            raise FileNotFoundError(f"File not found: {input_path}")

        try:
            df = self.pd.read_parquet(input_path)

            if format.lower() == "csv":
                df.to_csv(output_path, index=False)
            elif format.lower() == "json":
                df.to_json(output_path, orient="records", indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

            return output_path
        except Exception as e:
            raise RuntimeError(f"Error converting file: {e}")


def run_parquet_lab_logic(args):
    """
    CLI logic for Parquet Lab.
    """
    manager = ParquetLabManager(args.project_dir)

    try:
        if args.action == "read":
            if not args.file:
                print("Error: --file is required.", file=sys.stderr)
                sys.exit(1)

            content = manager.read_parquet(Path(args.file), limit=args.limit)
            print(content)

        elif args.action == "schema":
            if not args.file:
                print("Error: --file is required.", file=sys.stderr)
                sys.exit(1)

            info = manager.get_schema(Path(args.file))
            print(json.dumps(info, indent=2))

        elif args.action == "convert":
            if not args.file or not args.output:
                print("Error: --file and --output are required.", file=sys.stderr)
                sys.exit(1)

            manager.convert(Path(args.file), Path(args.output), args.format)
            print(f"✅ Converted {args.file} to {args.output} ({args.format})")

    except ImportError as e:
        print(f"❌ Dependency Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
