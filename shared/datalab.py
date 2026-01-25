import csv
import json
import statistics
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

class DataLabManager:
    """Manages data loading and analysis for the Data Lab."""

    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = project_dir

    def load_data(self, source: str, format: str = "auto") -> List[Dict[str, Any]]:
        """
        Loads data from a file path or raw string.
        Returns a list of dictionaries (records).
        """
        data = []
        source = source.strip()

        # Determine if source is a file path or raw data
        is_file = False
        try:
            path = Path(source)
            # If project_dir is set and path is relative, resolve it
            if self.project_dir and not path.is_absolute():
                path = self.project_dir / path

            if path.exists() and path.is_file():
                is_file = True
                content = path.read_text(encoding="utf-8")
                # Auto-detect format from extension if not specified
                if format == "auto":
                    if path.suffix.lower() == ".csv":
                        format = "csv"
                    elif path.suffix.lower() == ".json":
                        format = "json"
            else:
                content = source
        except OSError:
            content = source

        # If format is still auto, try to guess based on content
        if format == "auto":
            if content.strip().startswith("[") or content.strip().startswith("{"):
                format = "json"
            else:
                format = "csv" # Fallback

        try:
            if format == "json":
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    data = parsed
                elif isinstance(parsed, dict):
                    # Try to find a list value, or wrap dict in list
                    # Common pattern: {"data": [...]}
                    if "data" in parsed and isinstance(parsed["data"], list):
                        data = parsed["data"]
                    elif "items" in parsed and isinstance(parsed["items"], list):
                        data = parsed["items"]
                    else:
                        data = [parsed]

            elif format == "csv":
                # Use csv module
                reader = csv.DictReader(content.splitlines())
                data = list(reader)

                # Attempt to convert numeric strings to floats
                for row in data:
                    for k, v in row.items():
                        if v is None: continue
                        try:
                            if "." in v:
                                row[k] = float(v)
                            else:
                                row[k] = int(v)
                        except (ValueError, TypeError):
                            pass # Keep as string

        except Exception as e:
            raise ValueError(f"Failed to parse data as {format}: {e}")

        return data

    def get_columns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Returns a list of all unique keys found in the data."""
        if not data:
            return []

        # Aggregate keys from first few rows to be fast, or all rows to be accurate?
        # Let's check first 100 rows
        keys = set()
        for row in data[:100]:
            keys.update(row.keys())
        return sorted(list(keys))

    def analyze_column(self, data: List[Dict[str, Any]], column: str) -> Dict[str, Union[float, str]]:
        """Calculates statistics for a specific column."""
        values = []
        for row in data:
            val = row.get(column)
            if isinstance(val, (int, float)):
                values.append(val)
            elif isinstance(val, str):
                # Try to convert if it looks numeric
                try:
                    values.append(float(val))
                except ValueError:
                    pass

        if not values:
            return {"error": "No numeric data found in column."}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "sum": sum(values)
        }
