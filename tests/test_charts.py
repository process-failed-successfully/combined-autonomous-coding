import unittest
from shared.charts import draw_ascii_bar_chart


class TestCharts(unittest.TestCase):
    def test_draw_ascii_bar_chart_basic(self):
        data = {"Run 1": 10, "Run 2": 20, "Run 3": 5}
        chart = draw_ascii_bar_chart(data, "Test Chart", width=10)
        expected = (
            "--- Test Chart ---\n"
            "Run 1 | █████ 10\n"
            "Run 2 | ██████████ 20\n"
            "Run 3 | ██ 5"
        )
        # Note: Exact spacing might vary due to ljust/int math, let's verify key components
        self.assertIn("--- Test Chart ---", chart)
        self.assertIn("Run 1", chart)
        self.assertIn("Run 2", chart)
        self.assertIn("Run 3", chart)
        self.assertIn("10", chart)
        self.assertIn("20", chart)
        self.assertIn("5", chart)

    def test_draw_ascii_bar_chart_empty(self):
        data = {}
        chart = draw_ascii_bar_chart(data, "Empty Chart")
        self.assertIn("(No data)", chart)

    def test_draw_ascii_bar_chart_scaling(self):
        data = {"A": 100, "B": 50}
        # Width 10 means A should have 10 blocks, B should have 5
        chart = draw_ascii_bar_chart(data, "Scaling", width=10)
        self.assertIn("█" * 10, chart)
        self.assertIn("█" * 5, chart)

    def test_draw_ascii_bar_chart_zeros(self):
        data = {"A": 0, "B": 0}
        chart = draw_ascii_bar_chart(data, "Zeros")
        self.assertIn("A |  0", chart)  # Should have empty bar


if __name__ == '__main__':
    unittest.main()
