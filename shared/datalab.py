import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Union

class DataLabManager:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir

    def list_data_files(self) -> List[Path]:
        """Lists CSV and JSON files in the project directory."""
        extensions = ["*.csv", "*.json"]
        files = []
        for ext in extensions:
            files.extend(list(self.project_dir.glob(f"**/{ext}")))

        # Exclude hidden files and some common directories
        filtered_files = []
        for f in files:
            # Check if any part of the path starts with .
            if any(p.startswith(".") for p in f.parts):
                continue
            if "node_modules" in f.parts or "venv" in f.parts or "site-packages" in f.parts:
                continue
            filtered_files.append(f)

        return sorted(filtered_files)

    def load_file(self, filepath: Path) -> List[Dict[str, Any]]:
        """Loads data from a file."""
        if not filepath.exists():
            return []

        try:
            if filepath.suffix == ".json":
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        # Try to find a list in the dict, or return [data]
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                return value
                        return [data]
                    else:
                        return []
            elif filepath.suffix == ".csv":
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    # We need to handle potential errors with delimiters etc
                    reader = csv.DictReader(f)
                    return list(reader)
        except Exception:
            # Return empty list on error
            return []

        return []

    def get_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculates basic statistics for numeric columns."""
        if not data:
            return {}

        stats = {}
        # Get all keys from first row
        keys = data[0].keys()

        for key in keys:
            values = []
            for row in data:
                try:
                    val = row.get(key)
                    if val is None or val == "":
                        continue
                    # Handle numbers that might be strings
                    float_val = float(val)
                    values.append(float_val)
                except (ValueError, TypeError):
                    continue

            if values:
                stats[key] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values)
                }
        return stats
