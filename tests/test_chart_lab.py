import unittest
from unittest.mock import patch
from pathlib import Path
import json
import tempfile
import shutil
import io

from shared.chart_lab import ChartLabManager


class TestChartLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = ChartLabManager(width=50, height=10)
        self.test_dir = tempfile.mkdtemp()
        self.csv_file = Path(self.test_dir) / "test.csv"
        self.json_file = Path(self.test_dir) / "test.json"

        # Sample Data
        self.csv_content = "Name,Value\nA,10\nB,20\nC,30"
        self.csv_file.write_text(self.csv_content, encoding="utf-8")

        self.json_content = json.dumps([{"Name": "A", "Value": 10}, {"Name": "B", "Value": 20}])
        self.json_file.write_text(self.json_content, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_data_csv(self):
        data = self.manager.load_data(self.csv_file)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["Name"], "A")
        self.assertEqual(data[0]["Value"], "10")

    def test_load_data_json(self):
        data = self.manager.load_data(self.json_file)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["Name"], "A")
        self.assertEqual(data[0]["Value"], 10)

    @patch("sys.stdin", new_callable=io.StringIO)
    def test_load_data_stdin_csv(self, mock_stdin):
        mock_stdin.write(self.csv_content)
        mock_stdin.seek(0)

        # Simulate isatty=False for pipe
        with patch("sys.stdin.isatty", return_value=False):
            data = self.manager.load_data(None, format="csv")

        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["Name"], "A")

    @patch("sys.stdin", new_callable=io.StringIO)
    def test_load_data_stdin_json(self, mock_stdin):
        mock_stdin.write(self.json_content)
        mock_stdin.seek(0)

        with patch("sys.stdin.isatty", return_value=False):
            data = self.manager.load_data(None, format="json")

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["Name"], "A")

    def test_plot_bar(self):
        data = [{"Name": "A", "Value": 10}, {"Name": "B", "Value": 20}]
        output = self.manager.plot_bar(data, "Name", "Value")

        self.assertIn("Bar Chart: Value by Name", output)
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("█", output)  # Check for bar character

    def test_plot_scatter(self):
        data = [{"X": 1, "Y": 10}, {"X": 2, "Y": 20}]
        output = self.manager.plot_scatter(data, "X", "Y")

        self.assertIn("Scatter Plot: Y vs X", output)
        self.assertTrue("•" in output or "█" in output)

    def test_plot_line(self):
        data = [{"X": 1, "Y": 10}, {"X": 2, "Y": 20}]
        output = self.manager.plot_line(data, "X", "Y")
        self.assertIn("Line Chart", output)

    def test_missing_columns(self):
        data = [{"Name": "A"}]  # Missing Value
        output = self.manager.plot_bar(data, "Name", "Value")
        # Should still run but treat value as 0
        self.assertIn("A", output)


if __name__ == "__main__":
    unittest.main()
