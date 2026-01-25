import unittest
import tempfile
import os
import json
from pathlib import Path
from shared.datalab import DataLabManager

class TestDataLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = DataLabManager()

    def test_load_csv_string(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        data = self.manager.load_data(csv_data, format="csv")
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        self.assertEqual(data[0]["age"], 30)

    def test_load_json_string(self):
        json_data = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
        data = self.manager.load_data(json_data, format="json")
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["age"], 30)

    def test_load_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('[{"x": 1, "y": 2}]')
            temp_name = f.name

        try:
            data = self.manager.load_data(temp_name)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["x"], 1)
        finally:
            os.remove(temp_name)

    def test_get_columns(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "c": 4}]
        cols = self.manager.get_columns(data)
        self.assertEqual(sorted(cols), ["a", "b", "c"])

    def test_analyze_column(self):
        data = [
            {"val": 10},
            {"val": 20},
            {"val": 30},
            {"val": "not num"}, # Should be ignored
            {"other": 5} # Missing key
        ]
        stats = self.manager.analyze_column(data, "val")
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["min"], 10)
        self.assertEqual(stats["max"], 30)
        self.assertEqual(stats["mean"], 20)
        self.assertEqual(stats["median"], 20)

    def test_auto_detect_csv(self):
        csv_data = "col1,col2\n1,2"
        data = self.manager.load_data(csv_data) # Auto
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["col1"], 1)

if __name__ == "__main__":
    unittest.main()
