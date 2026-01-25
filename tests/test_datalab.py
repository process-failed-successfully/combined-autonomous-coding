import unittest
from pathlib import Path
import json
import csv
import tempfile
import shutil
from shared.datalab import DataLabManager

class TestDataLabManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = DataLabManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_list_data_files(self):
        # Create some files
        (self.test_dir / "data1.csv").touch()
        (self.test_dir / "data2.json").touch()
        (self.test_dir / "ignore.txt").touch()

        # Create a hidden dir
        hidden_dir = self.test_dir / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "hidden.csv").touch()

        # Create venv
        venv_dir = self.test_dir / "venv"
        venv_dir.mkdir()
        (venv_dir / "venv.json").touch()

        files = self.manager.list_data_files()
        filenames = [f.name for f in files]

        self.assertIn("data1.csv", filenames)
        self.assertIn("data2.json", filenames)
        self.assertNotIn("ignore.txt", filenames)
        self.assertNotIn("hidden.csv", filenames)
        self.assertNotIn("venv.json", filenames)

    def test_load_file_csv(self):
        csv_file = self.test_dir / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "age"])
            writer.writerow(["Alice", "30"])
            writer.writerow(["Bob", "25"])

        data = self.manager.load_file(csv_file)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        self.assertEqual(data[0]["age"], "30")

    def test_load_file_json_list(self):
        json_file = self.test_dir / "test.json"
        content = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        with open(json_file, "w") as f:
            json.dump(content, f)

        data = self.manager.load_file(json_file)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")

    def test_load_file_json_dict_wrapper(self):
        # Some JSON APIs return { "data": [...] }
        json_file = self.test_dir / "wrapped.json"
        content = {"results": [{"id": 1}, {"id": 2}]}
        with open(json_file, "w") as f:
            json.dump(content, f)

        data = self.manager.load_file(json_file)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], 1)

    def test_get_statistics(self):
        data = [
            {"name": "A", "score": 10, "empty": ""},
            {"name": "B", "score": "20", "empty": None}, # Mixed types
            {"name": "C", "score": 30},
            {"name": "D", "score": "invalid"}
        ]

        stats = self.manager.get_statistics(data)

        self.assertIn("score", stats)
        self.assertEqual(stats["score"]["count"], 3) # 10, 20, 30. "invalid" ignored.
        self.assertEqual(stats["score"]["min"], 10)
        self.assertEqual(stats["score"]["max"], 30)
        self.assertEqual(stats["score"]["mean"], 20)

        self.assertNotIn("name", stats)
        self.assertNotIn("empty", stats)

if __name__ == "__main__":
    unittest.main()
