import csv
import json
import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from rich.console import Console
from rich.bar import Bar
from rich.text import Text

class DataLoader:
    @staticmethod
    def load(source: Union[str, Path]) -> List[Dict[str, Any]]:
        """Loads data from CSV, JSON, or stdin."""
        data = []
        content = ""

        if str(source) == "-":
            try:
                content = sys.stdin.read()
            except Exception:
                raise ValueError("Error reading from stdin.")
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            content = path.read_text(encoding="utf-8")

        if not content.strip():
             raise ValueError("Input data is empty.")

        # Try JSON first
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try CSV
            try:
                reader = csv.DictReader(content.splitlines())
                data = list(reader)
            except Exception:
                raise ValueError("Could not parse data as JSON or CSV.")

        if isinstance(data, dict):
             return [{"key": k, "value": v} for k, v in data.items()]

        if not isinstance(data, list):
            raise ValueError("Data must be a list of records (JSON array or CSV rows).")

        if not data:
            raise ValueError("Data list is empty.")

        return data

class BrailleChart:
    """
    Renders a high-resolution line chart using Unicode Braille characters.
    Each character is a 2x4 dot matrix.
    """
    BRAILLE_OFFSET = 0x2800

    DOT_MAP = {
        (0, 0): 0x1,
        (0, 1): 0x2,
        (0, 2): 0x4,
        (0, 3): 0x40,
        (1, 0): 0x8,
        (1, 1): 0x10,
        (1, 2): 0x20,
        (1, 3): 0x80,
    }

    def __init__(self, width: int = 60, height: int = 15):
        self.width = width
        self.height = height

    def render(self, x_values: List[Any], y_values: List[float], title: str = "") -> str:
        if not y_values:
            return "(No data)"

        min_y = min(y_values)
        max_y = max(y_values)

        if min_y == max_y:
            min_y -= 1
            max_y += 1

        range_y = max_y - min_y

        canvas_w = self.width * 2
        canvas_h = self.height * 4

        dots: Set[Tuple[int, int]] = set()
        count = len(y_values)

        for i in range(count - 1):
            y1 = y_values[i]
            y2 = y_values[i+1]

            x1_canvas = int(i * (canvas_w - 1) / (count - 1))
            x2_canvas = int((i + 1) * (canvas_w - 1) / (count - 1))

            y1_canvas = int((y1 - min_y) / range_y * (canvas_h - 1))
            y2_canvas = int((y2 - min_y) / range_y * (canvas_h - 1))

            self._draw_line(dots, x1_canvas, y1_canvas, x2_canvas, y2_canvas)

        if count == 1:
             y1 = y_values[0]
             x1_canvas = int((canvas_w - 1) / 2)
             y1_canvas = int((y1 - min_y) / range_y * (canvas_h - 1))
             dots.add((x1_canvas, y1_canvas))

        lines = []
        if title:
            lines.append(f"[bold]{title}[/bold]")

        for r in range(self.height):
            label_width = 10
            label = " " * label_width
            if r == 0:
                label = f"{max_y:>{label_width}.2f} "
            elif r == self.height - 1:
                label = f"{min_y:>{label_width}.2f} "

            row_str = ""
            for c in range(self.width):
                base_val = self.BRAILLE_OFFSET
                char_top_canvas_y = canvas_h - 1 - (r * 4)
                char_left_canvas_x = c * 2

                for (d_col, d_row), val in self.DOT_MAP.items():
                    dot_x = char_left_canvas_x + d_col
                    dot_y = char_top_canvas_y - d_row

                    if (dot_x, dot_y) in dots:
                        base_val += val

                row_str += chr(base_val)

            lines.append(f"{label}{row_str}")

        return "\n".join(lines)

    def _draw_line(self, dots, x1, y1, x2, y2):
        """Bresenham's line algorithm."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            dots.add((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

class Visualizer:
    def __init__(self):
        self.console = Console()

    def visualize(self, data: List[Dict[str, Any]], chart_type: str = "bar", x_key: str = None, y_key: str = None, title: str = "", width: int = 60, height: int = 20):
        if not data:
            self.console.print("No data to visualize.")
            return

        keys = list(data[0].keys())
        if not x_key:
            x_key = keys[0]
        if not y_key:
            for k in keys:
                if k != x_key and self._is_numeric(data[0].get(k)):
                    y_key = k
                    break
            if not y_key and len(keys) > 1:
                y_key = keys[1]

        if not y_key:
            self.console.print("[red]Error: Could not automatically determine a Y-axis column. Please specify with --y.[/red]")
            return

        x_vals = []
        y_vals = []

        for item in data:
            try:
                y = float(item.get(y_key, 0))
                x = item.get(x_key, "")
                x_vals.append(x)
                y_vals.append(y)
            except (ValueError, TypeError):
                continue

        if not y_vals:
            self.console.print(f"[red]Error: No valid numeric data found for column '{y_key}'.[/red]")
            return

        if not title:
            title = f"{y_key} vs {x_key}"

        if chart_type == "bar":
            self._render_bar(x_vals, y_vals, title, width, height)
        elif chart_type == "line":
            self._render_line(x_vals, y_vals, title, width, height)
        elif chart_type == "pie":
             self._render_pie(x_vals, y_vals, title)
        elif chart_type == "scatter":
            self._render_line(x_vals, y_vals, title, width, height)
        else:
            self.console.print(f"Unknown chart type: {chart_type}")

    def _is_numeric(self, val):
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

    def _render_bar(self, x_vals, y_vals, title, width, height):
        self.console.print(f"[bold]{title}[/bold]")

        if not y_vals:
            return

        max_val = max(y_vals)
        if max_val == 0:
            max_val = 1

        limit = max(10, height) # Use height for number of bars to show in vertical list
        if len(x_vals) > limit:
             self.console.print(f"[yellow]Note: Showing first {limit} items out of {len(x_vals)}.[/yellow]")
             x_vals = x_vals[:limit]
             y_vals = y_vals[:limit]

        # Find label max width
        max_len = 0
        for x in x_vals:
            max_len = max(max_len, len(str(x)))

        for x, y in zip(x_vals, y_vals):
            # Rich Bar widget usage: Bar(size, begin, end, width)
            # We want end=y. size=max_val. begin=0.

            # Since Rich 13+ doesn't have a full chart widget (only Bar), we simulate one.
            bar = Bar(size=max_val, begin=0, end=y, width=width)

            label = str(x).rjust(max_len)
            self.console.print(f"{label} ", end="")
            self.console.print(bar, end=" ")
            self.console.print(f"{y}")


    def _render_line(self, x_vals, y_vals, title, width, height):
        chart = BrailleChart(width=width, height=height)
        output = chart.render(x_vals, y_vals, title)
        self.console.print(output)

    def _render_pie(self, x_vals, y_vals, title):
        total = sum(y_vals)
        if total == 0:
            return

        self.console.print(f"[bold]{title}[/bold]")

        combined = sorted(zip(x_vals, y_vals), key=lambda p: p[1], reverse=True)

        if len(combined) > 10:
            others = combined[10:]
            combined = combined[:10]
            others_sum = sum(v for _, v in others)
            combined.append(("Others", others_sum))

        for label, val in combined:
            pct = (val / total) * 100
            bar_len = int(pct / 2) # 50 chars = 100%
            bar = "█" * bar_len
            self.console.print(f"{str(label):<20} | {bar} {val:.2f} ({pct:.1f}%)")

def run_visualize(args):
    """Entry point for CLI visualization."""
    from rich.console import Console
    console = Console()

    loader = DataLoader()
    try:
        data = loader.load(args.data)
    except Exception as e:
        console.print(f"[red]Error loading data: {e}[/red]")
        sys.exit(1)

    viz = Visualizer()
    viz.visualize(
        data,
        chart_type=args.type,
        x_key=args.x,
        y_key=args.y,
        title=args.title,
        width=args.width,
        height=args.height
    )
