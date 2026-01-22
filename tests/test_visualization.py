import unittest
import json
import tempfile
from pathlib import Path
from shared.visualization import DataLoader, BrailleChart


class TestVisualization(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dataloader_json(self):
        data = [{"name": "A", "val": 10}, {"name": "B", "val": 20}]
        json_file = self.temp_path / "data.json"
        with open(json_file, "w") as f:
            json.dump(data, f)

        loaded = DataLoader.load(json_file)
        self.assertEqual(loaded, data)

    def test_dataloader_csv(self):
        csv_file = self.temp_path / "data.csv"
        with open(csv_file, "w") as f:
            f.write("name,val\nA,10\nB,20")

        loaded = DataLoader.load(csv_file)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["name"], "A")
        self.assertEqual(loaded[0]["val"], "10")

    def test_dataloader_dict(self):
        data = {"A": 10, "B": 20}
        json_file = self.temp_path / "dict.json"
        with open(json_file, "w") as f:
            json.dump(data, f)

        loaded = DataLoader.load(json_file)
        self.assertEqual(len(loaded), 2)
        # Should be normalized to list of kv pairs
        self.assertEqual(loaded[0]["key"], "A")
        self.assertEqual(loaded[0]["value"], 10)

    def test_braille_chart_rendering(self):
        chart = BrailleChart(width=10, height=5)
        # Simple line from 0 to 10
        y_vals = [float(i) for i in range(11)]
        x_vals = list(range(11))

        output = chart.render(x_vals, y_vals, title="Test Line")

        self.assertIn("Test Line", output)
        # Check for presence of Braille characters (Unicode range 0x2800 - 0x28FF)
        has_braille = any(0x2800 <= ord(c) <= 0x28FF for c in output)
        self.assertTrue(has_braille, "Output should contain Braille characters")

    def test_braille_chart_single_point(self):
        chart = BrailleChart(width=10, height=5)
        output = chart.render(["A"], [5.0], title="Single")
        self.assertIn("Single", output)
        has_braille = any(0x2800 <= ord(c) <= 0x28FF for c in output)
        self.assertTrue(has_braille)


if __name__ == '__main__':
    unittest.main()
