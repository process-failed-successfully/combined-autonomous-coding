import csv
import json
import sys
import shutil
import math
from typing import List, Dict, Any, Union, Optional
from pathlib import Path

class ChartLabManager:
    """
    Manages data loading and chart generation for ASCII/Unicode plots.
    """

    def __init__(self, width: int = 80, height: int = 20):
        self.width = width
        self.height = height

    def load_data(self, source: Union[str, Path, None], format: str = "auto") -> List[Dict[str, Any]]:
        """
        Loads data from a file or stdin.
        """
        data = []
        content = ""

        # Determine source content
        if source and str(source) != "-":
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            content = path.read_text(encoding="utf-8")
            if format == "auto":
                if path.suffix.lower() == ".json":
                    format = "json"
                else:
                    format = "csv"
        else:
            # Read from stdin
            if sys.stdin.isatty():
                raise ValueError("No input provided (pipe data or specify file).")
            content = sys.stdin.read()
            if format == "auto":
                # Simple heuristic
                if content.strip().startswith(("[", "{")):
                    format = "json"
                else:
                    format = "csv"

        # Parse content
        try:
            if format == "json":
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    data = parsed
                elif isinstance(parsed, dict):
                    # Maybe it's {"data": [...]} or just a single object?
                    # Let's assume list of objects for now, or single object wrapped
                    data = [parsed]
            else: # CSV
                reader = csv.DictReader(content.splitlines())
                data = list(reader)
        except Exception as e:
            raise ValueError(f"Error parsing data as {format}: {e}")

        return data

    def _get_column_values(self, data: List[Dict[str, Any]], col: str, numeric: bool = False) -> List[Any]:
        """Extracts values from a column, optionally converting to float."""
        values = []
        for row in data:
            val = row.get(col)
            if numeric:
                try:
                    val = float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    val = 0.0
            values.append(val)
        return values

    def plot_bar(self, data: List[Dict[str, Any]], x_col: str, y_col: str) -> str:
        """
        Generates a horizontal bar chart.
        x_col: Label column
        y_col: Value column (numeric)
        """
        if not data:
            return "No data to plot."

        labels = self._get_column_values(data, x_col)
        values = self._get_column_values(data, y_col, numeric=True)

        if not values:
            return "No numeric data found for Y column."

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min(0, min_val) # Ensure 0 is included if data is positive

        if range_val == 0:
            range_val = 1

        # Determine label width
        max_label_len = max((len(str(l)) for l in labels), default=0)
        max_label_len = min(max_label_len, 20) # Cap label width

        # Chart width available for bars
        bar_width = self.width - max_label_len - 10 # Reserve space for label and value text

        output = []
        output.append(f"Bar Chart: {y_col} by {x_col}")
        output.append("-" * self.width)

        for label, value in zip(labels, values):
            # Calculate bar length
            # Normalize value relative to max_val
            if value >= 0:
                normalized = value / max_val if max_val > 0 else 0
            else:
                normalized = 0 # Handle negative? For simple bar, maybe just 0

            length = int(normalized * bar_width)
            bar = "█" * length

            # Format label
            label_str = str(label)
            if len(label_str) > max_label_len:
                label_str = label_str[:max_label_len-3] + "..."

            output.append(f"{label_str:<{max_label_len}} | {bar} {value}")

        return "\n".join(output)

    def plot_scatter(self, data: List[Dict[str, Any]], x_col: str, y_col: str) -> str:
        """
        Generates a scatter plot.
        x_col: Numeric
        y_col: Numeric
        """
        if not data:
            return "No data to plot."

        x_values = self._get_column_values(data, x_col, numeric=True)
        y_values = self._get_column_values(data, y_col, numeric=True)

        if not x_values or not y_values:
            return "No numeric data found."

        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1

        # Canvas size
        # We use a grid of characters
        grid_w = self.width - 10
        grid_h = self.height - 4

        grid = [[' ' for _ in range(grid_w)] for _ in range(grid_h)]

        for x, y in zip(x_values, y_values):
            # Map to grid coordinates
            # Y is inverted (row 0 is top)
            col = int((x - min_x) / range_x * (grid_w - 1))
            row = int((max_y - y) / range_y * (grid_h - 1)) # Invert Y

            # Clamp
            col = max(0, min(grid_w - 1, col))
            row = max(0, min(grid_h - 1, row))

            if grid[row][col] == ' ':
                grid[row][col] = '•'
            else:
                grid[row][col] = '█' # Overlap

        output = []
        output.append(f"Scatter Plot: {y_col} vs {x_col}")

        # Y-axis top label
        output.append(f"{max_y:.2f} +")

        for i, row in enumerate(grid):
            prefix = "      |"
            if i == grid_h // 2:
                prefix = f"{min_y + (max_y - min_y)/2:5.2f} |" # Mid label

            output.append(prefix + "".join(row))

        # X-axis
        output.append("      +" + "-" * grid_w)
        output.append(f"      {min_x:<{grid_w//2}.2f}{max_x:>{grid_w//2}.2f}")

        return "\n".join(output)

    def plot_line(self, data: List[Dict[str, Any]], x_col: str, y_col: str) -> str:
        """
        Generates a simple line chart (using scatter logic but connecting dots logic is hard in ASCII).
        For now, implementing as scatter with sorted X.
        """
        # Sort by X
        combined = sorted(zip(self._get_column_values(data, x_col, numeric=True),
                              self._get_column_values(data, y_col, numeric=True)))

        # Reconstruct sorted dicts just for the plotter?
        # Actually simpler to just reuse scatter logic but maybe use different char
        # Or implement a distinct line renderer if we want to "connect" points (e.g. using / \ | -)

        # For MVP, let's reuse scatter with '*' and indicate it's a line chart
        return self.plot_scatter(data, x_col, y_col).replace("Scatter Plot", "Line Chart (Scatter View)")

def run_chart_lab_logic(args):
    """
    CLI Entry point for Chart Lab.
    """
    # Detect terminal size if not provided
    term_size = shutil.get_terminal_size((80, 20))
    width = args.width if args.width else term_size.columns
    height = args.height if args.height else term_size.lines

    manager = ChartLabManager(width=width, height=height)

    try:
        data = manager.load_data(args.file)
    except Exception as e:
        print(f"❌ Error loading data: {e}", file=sys.stderr)
        sys.exit(1)

    if args.action == "bar":
        print(manager.plot_bar(data, args.x, args.y))
    elif args.action == "scatter":
        print(manager.plot_scatter(data, args.x, args.y))
    elif args.action == "line":
        print(manager.plot_line(data, args.x, args.y))
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
