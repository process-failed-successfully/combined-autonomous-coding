import unittest
from shared.charts import draw_ascii_bar_chart, draw_ascii_line_chart, draw_ascii_scatter_chart

class TestCharts(unittest.TestCase):
    def test_draw_ascii_bar_chart(self):
        data = {"A": 10, "B": 20, "C": 5}
        chart = draw_ascii_bar_chart(data, "Test Chart", width=10)
        self.assertIn("Test Chart", chart)
        self.assertIn("A", chart)
        self.assertIn("B", chart)
        self.assertIn("C", chart)
        self.assertIn("█", chart)

    def test_draw_ascii_line_chart(self):
        data = [1.0, 2.0, 3.0, 2.0, 1.0]
        chart = draw_ascii_line_chart(data, width=10, height=5)
        self.assertIn("(Min: 1.00, Max: 3.00)", chart)
        # Check for unicode Braille characters range
        # At least one char > 0x2800 should be present
        found_braille = False
        for char in chart:
            if 0x2800 <= ord(char) <= 0x28FF:
                found_braille = True
                break
        self.assertTrue(found_braille, "No Braille characters found in line chart")

    def test_draw_ascii_scatter_chart(self):
        points = [(0, 0), (1, 1), (2, 2)]
        chart = draw_ascii_scatter_chart(points, width=10, height=5)
        self.assertIn("X: 0.00 - 2.00", chart)

        found_braille = False
        for char in chart:
            if 0x2800 <= ord(char) <= 0x28FF:
                found_braille = True
                break
        self.assertTrue(found_braille, "No Braille characters found in scatter chart")

    def test_empty_charts(self):
        self.assertIn("No data", draw_ascii_bar_chart({}, "Empty"))
        self.assertIn("No data", draw_ascii_line_chart([]))
        self.assertIn("No data", draw_ascii_scatter_chart([]))

if __name__ == "__main__":
    unittest.main()
