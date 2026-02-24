import unittest
from pathlib import Path
from shared.diagram_lab import DiagramLabManager

class TestDiagramLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = DiagramLabManager(width=10, height=5)

    def test_initialization(self):
        self.assertEqual(self.manager.width, 10)
        self.assertEqual(self.manager.height, 5)
        self.assertEqual(len(self.manager.canvas), 5)
        self.assertEqual(len(self.manager.canvas[0]), 10)
        self.assertEqual(self.manager.canvas[0][0], " ")

    def test_draw_char(self):
        self.manager.draw_char(0, 0, "X")
        self.assertEqual(self.manager.canvas[0][0], "X")

        # Out of bounds
        self.manager.draw_char(10, 0, "Y") # Should not crash
        self.manager.draw_char(0, 5, "Z") # Should not crash

    def test_draw_line_horizontal(self):
        self.manager.draw_line(1, 1, 5, 1, style="light")
        expected = "─"
        for x in range(1, 6):
            self.assertEqual(self.manager.canvas[1][x], expected)

    def test_draw_line_vertical(self):
        self.manager.draw_line(1, 1, 1, 3, style="light")
        expected = "│"
        for y in range(1, 4):
            self.assertEqual(self.manager.canvas[y][1], expected)

    def test_draw_box(self):
        self.manager.draw_box(1, 1, 3, 3, style="light")
        # 1,1 should be TL corner
        self.assertEqual(self.manager.canvas[1][1], "┌")
        self.assertEqual(self.manager.canvas[1][3], "┐")
        self.assertEqual(self.manager.canvas[3][1], "└")
        self.assertEqual(self.manager.canvas[3][3], "┘")
        self.assertEqual(self.manager.canvas[1][2], "─")
        self.assertEqual(self.manager.canvas[2][1], "│")

    def test_write_text(self):
        self.manager.write_text(1, 1, "Hello")
        self.assertEqual(self.manager.canvas[1][1], "H")
        self.assertEqual(self.manager.canvas[1][2], "e")
        self.assertEqual(self.manager.canvas[1][5], "o")

    def test_render(self):
        self.manager.write_text(0, 0, "Hi")
        rendered = self.manager.render()
        lines = rendered.splitlines()
        self.assertEqual(lines[0][:2], "Hi")
        self.assertEqual(len(lines), 5)

    def test_resize(self):
        self.manager.write_text(0, 0, "Hello")
        self.manager.resize(5, 5) # Crop width
        self.assertEqual(self.manager.width, 5)
        self.assertEqual(len(self.manager.canvas[0]), 5)
        rendered = self.manager.render().splitlines()
        self.assertEqual(rendered[0], "Hello")

        self.manager.resize(10, 5) # Expand width
        self.assertEqual(self.manager.width, 10)
        self.assertEqual(self.manager.canvas[0][5], " ") # New space

    def test_clear(self):
        self.manager.write_text(0, 0, "Hello")
        self.manager.clear()
        self.assertEqual(self.manager.canvas[0][0], " ")

    def test_save_load(self):
        import tempfile
        import os

        self.manager.write_text(0, 0, "SaveLoad")

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            path = Path(tmp.name)

        try:
            self.manager.save(path)

            # Create new manager
            new_mgr = DiagramLabManager()
            content = path.read_text(encoding="utf-8")
            new_mgr.load(content)

            self.assertEqual(new_mgr.canvas[0][0], "S")
            self.assertEqual(new_mgr.canvas[0][7], "d")
        finally:
            if path.exists():
                os.unlink(path)

if __name__ == '__main__':
    unittest.main()
