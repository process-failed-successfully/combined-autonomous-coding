from typing import Dict, List, Optional, Tuple
import math

def draw_ascii_bar_chart(data: Dict[str, float], title: str, width: int = 60, color: str = "blue") -> str:
    """
    Generates an ASCII bar chart from the provided data.

    Args:
        data: A dictionary where keys are labels and values are numeric.
        title: The title of the chart.
        width: The max width of the bars (excluding labels).
        color: The rich color tag to use for bars (e.g., "blue", "green").

    Returns:
        A string representing the chart.
    """
    if not data:
        return f"{title}\n(No data)"

    # Determine max value for scaling
    max_val = max(data.values()) if data.values() else 0
    if max_val == 0:
        max_val = 1  # Avoid division by zero

    # Determine max label length for alignment
    max_label_len = max(len(str(k)) for k in data.keys())

    lines = [f"--- {title} ---"]

    for label, value in data.items():
        # Calculate bar length
        bar_len = int((value / max_val) * width)
        bar = "█" * bar_len

        # Format label
        label_str = str(label).ljust(max_label_len)

        # Apply rich styling
        styled_bar = f"[{color}]{bar}[/{color}]"

        lines.append(f"{label_str} | {styled_bar} {value}")

    return "\n".join(lines)


class BrailleCanvas:
    """A simple canvas for drawing using Braille characters (2x4 dots)."""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # grid is a list of lists of integers (mask)
        # We need width/2 columns and height/4 rows of characters
        self.cols = math.ceil(width / 2)
        self.rows = math.ceil(height / 4)
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]

    def set_pixel(self, x: int, y: int):
        """Sets a pixel at (x, y). Origin is bottom-left (0,0)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return

        # Y is flipped for storage (0 is top in list, but we want 0 at bottom)
        # So we invert y for calculation relative to top-left of the logical grid
        # Actually let's keep logical 0,0 at bottom-left

        # Braille dot mapping (standard)
        #   1  4
        #   2  5
        #   3  6
        #   7  8

        # Maps to offsets:
        # (0,0) -> 1 (0x1)
        # (0,1) -> 2 (0x2)
        # (0,2) -> 3 (0x4)
        # (0,3) -> 7 (0x40)
        # (1,0) -> 4 (0x8)
        # (1,1) -> 5 (0x10)
        # (1,2) -> 6 (0x20)
        # (1,3) -> 8 (0x80)

        col = x // 2
        row = (self.height - 1 - y) // 4 # Invert Y so 0 is at bottom

        sub_x = x % 2
        sub_y = (self.height - 1 - y) % 4

        # But wait, within a character, top row is row 0.
        # If y=0 (bottom), and height=4. row=(3-0)//4 = 0.
        # sub_y = 3.
        # If sub_y is 3 (bottom of char), we want dot 7 or 8.
        # If sub_y is 0 (top of char), we want dot 1 or 4.

        # Let's verify standard Braille mapping relative to top-left of character:
        # (0,0): 0x1, (1,0): 0x8
        # (0,1): 0x2, (1,1): 0x10
        # (0,2): 0x4, (1,2): 0x20
        # (0,3): 0x40, (1,3): 0x80

        # Correct sub_y calculation relative to top of the character block:
        # y_from_top = (self.height - 1 - y)
        # row = y_from_top // 4
        # sub_y_in_char = y_from_top % 4

        y_from_top = (self.height - 1 - y)
        char_row = y_from_top // 4
        sub_y = y_from_top % 4
        sub_x = x % 2

        mask = 0
        if sub_x == 0:
            if sub_y == 0: mask = 0x1
            elif sub_y == 1: mask = 0x2
            elif sub_y == 2: mask = 0x4
            elif sub_y == 3: mask = 0x40
        else:
            if sub_y == 0: mask = 0x8
            elif sub_y == 1: mask = 0x10
            elif sub_y == 2: mask = 0x20
            elif sub_y == 3: mask = 0x80

        if 0 <= char_row < self.rows and 0 <= col < self.cols:
            self.grid[char_row][col] |= mask

    def render(self) -> str:
        lines = []
        for r in range(self.rows):
            line = ""
            for c in range(self.cols):
                val = self.grid[r][c]
                # Braille pattern start is 0x2800
                line += chr(0x2800 + val)
            lines.append(line)
        return "\n".join(lines)


def draw_ascii_line_chart(data: List[float], labels: List[str] = None, height: int = 15, width: int = 60, color: str = "green") -> str:
    """
    Draws a line chart using Braille characters.

    Args:
        data: List of numerical values.
        labels: List of labels (optional, not fully supported in simple version).
        height: Height in characters (resolution * 4).
        width: Width in characters (resolution * 2).
        color: Rich color tag.
    """
    if not data:
        return "(No data)"

    min_val = min(data)
    max_val = max(data)
    if max_val == min_val:
        max_val += 1

    range_val = max_val - min_val

    # Canvas resolution
    res_w = width * 2
    res_h = height * 4

    canvas = BrailleCanvas(res_w, res_h)

    # Scale points
    points = []
    for i, val in enumerate(data):
        # x is proportional to index
        x = int((i / (len(data) - 1)) * (res_w - 1)) if len(data) > 1 else 0

        # y is proportional to value (relative to min)
        # normalized 0..1
        norm = (val - min_val) / range_val
        y = int(norm * (res_h - 1))
        points.append((x, y))

    # Draw lines between points
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i+1]

        # Bresenham's line algorithm
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            canvas.set_pixel(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    chart = canvas.render()
    return f"[{color}]{chart}[/{color}]\n(Min: {min_val:.2f}, Max: {max_val:.2f})"


def draw_ascii_scatter_chart(points: List[Tuple[float, float]], width: int = 60, height: int = 15, color: str = "yellow") -> str:
    """
    Draws a scatter chart.

    Args:
        points: List of (x, y) tuples.
    """
    if not points:
        return "(No data)"

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    if max_x == min_x: max_x += 1
    if max_y == min_y: max_y += 1

    res_w = width * 2
    res_h = height * 4

    canvas = BrailleCanvas(res_w, res_h)

    for x, y in points:
        px = int(((x - min_x) / (max_x - min_x)) * (res_w - 1))
        py = int(((y - min_y) / (max_y - min_y)) * (res_h - 1))
        canvas.set_pixel(px, py)

    chart = canvas.render()
    return f"[{color}]{chart}[/{color}]\nX: {min_x:.2f} - {max_x:.2f}, Y: {min_y:.2f} - {max_y:.2f}"
