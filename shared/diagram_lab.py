from typing import List, Optional
from pathlib import Path

class DiagramLabManager:
    """
    Manages ASCII diagram creation and manipulation.
    """

    STYLES = {
        "light": {
            "h": "─", "v": "│",
            "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
            "vl": "┤", "vr": "├", "ht": "┴", "hb": "┬", "c": "┼"
        },
        "heavy": {
            "h": "━", "v": "┃",
            "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
            "vl": "┫", "vr": "┣", "ht": "┻", "hb": "┳", "c": "╋"
        },
        "double": {
            "h": "═", "v": "║",
            "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
            "vl": "╣", "vr": "╠", "ht": "╩", "hb": "╦", "c": "╬"
        },
        "rounded": {
            "h": "─", "v": "│",
            "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
            "vl": "┤", "vr": "├", "ht": "┴", "hb": "┬", "c": "┼"
        },
        "ascii": {
            "h": "-", "v": "|",
            "tl": "+", "tr": "+", "bl": "+", "br": "+",
            "vl": "+", "vr": "+", "ht": "+", "hb": "+", "c": "+"
        }
    }

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.canvas = [[" " for _ in range(width)] for _ in range(height)]

    def resize(self, width: int, height: int) -> None:
        """Resizes the canvas, preserving content where possible."""
        new_canvas = [[" " for _ in range(width)] for _ in range(height)]
        for y in range(min(self.height, height)):
            for x in range(min(self.width, width)):
                new_canvas[y][x] = self.canvas[y][x]
        self.width = width
        self.height = height
        self.canvas = new_canvas

    def clear(self) -> None:
        """Clears the canvas."""
        self.canvas = [[" " for _ in range(self.width)] for _ in range(self.height)]

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def draw_char(self, x: int, y: int, char: str) -> None:
        """Draws a single character at (x, y)."""
        if self._in_bounds(x, y):
            self.canvas[y][x] = char

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, style: str = "light") -> None:
        """Draws a horizontal or vertical line."""
        chars = self.STYLES.get(style, self.STYLES["light"])

        if x1 == x2:  # Vertical
            start_y, end_y = min(y1, y2), max(y1, y2)
            for y in range(start_y, end_y + 1):
                self.draw_char(x1, y, chars["v"])
        elif y1 == y2:  # Horizontal
            start_x, end_x = min(x1, x2), max(x1, x2)
            for x in range(start_x, end_x + 1):
                self.draw_char(x, y1, chars["h"])
        else:
            # Diagonal or arbitrary lines not supported properly with box chars yet
            # Fallback to simple Bresenham-like with 'x' or similar?
            # For now, just ignore or do crude steps.
            pass

    def draw_box(self, x1: int, y1: int, x2: int, y2: int, style: str = "light") -> None:
        """Draws a box defined by top-left (x1, y1) and bottom-right (x2, y2)."""
        chars = self.STYLES.get(style, self.STYLES["light"])

        start_x, end_x = min(x1, x2), max(x1, x2)
        start_y, end_y = min(y1, y2), max(y1, y2)

        # Corners
        self.draw_char(start_x, start_y, chars["tl"])
        self.draw_char(end_x, start_y, chars["tr"])
        self.draw_char(start_x, end_y, chars["bl"])
        self.draw_char(end_x, end_y, chars["br"])

        # Horizontal sides
        for x in range(start_x + 1, end_x):
            self.draw_char(x, start_y, chars["h"])
            self.draw_char(x, end_y, chars["h"])

        # Vertical sides
        for y in range(start_y + 1, end_y):
            self.draw_char(start_x, y, chars["v"])
            self.draw_char(end_x, y, chars["v"])

    def write_text(self, x: int, y: int, text: str) -> None:
        """Writes text starting at (x, y)."""
        for i, char in enumerate(text):
            self.draw_char(x + i, y, char)

    def render(self) -> str:
        """Renders the canvas to a string."""
        return "\n".join("".join(row) for row in self.canvas)

    def save(self, path: Path) -> None:
        """Saves the diagram to a file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.render())

    def load(self, content: str) -> None:
        """Loads a diagram from a string."""
        lines = content.splitlines()
        if not lines:
            return

        height = len(lines)
        width = max(len(line) for line in lines)

        self.resize(width, height)
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                self.draw_char(x, y, char)

def run_diagram_lab_logic(args):
    """
    CLI Entry point for Diagram Lab.
    Currently just prints a demo as interactive mode is TUI-only.
    """
    manager = DiagramLabManager(40, 10)
    manager.draw_box(2, 2, 38, 8, style="double")
    manager.write_text(5, 4, "Hello from Diagram Lab!")
    print(manager.render())
