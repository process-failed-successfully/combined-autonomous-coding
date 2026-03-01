import unittest
import json
import yaml
import csv
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from shared.data_lab import DataLabManager
from main import run_data_lab

class TestDataLabManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.manager = DataLabManager(self.project_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_and_convert_json_to_yaml(self):
        source_file = self.project_dir / "test.json"
        data = {"key": "value", "list": [1, 2, 3]}
        with open(source_file, "w") as f:
            json.dump(data, f)

        # Convert to string
        yaml_str = self.manager.convert(source_file, "yaml")
        self.assertIn("key: value", yaml_str)
        self.assertIn("- 1", yaml_str)

        # Convert to file
        output_file = self.project_dir / "output.yaml"
        self.manager.convert(source_file, "yaml", output_file)
        self.assertTrue(output_file.exists())

        with open(output_file, "r") as f:
            loaded_yaml = yaml.safe_load(f)
        self.assertEqual(loaded_yaml, data)

    def test_convert_csv_to_json(self):
        source_file = self.project_dir / "test.csv"
        with open(source_file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "age"])
            writer.writerow(["Alice", "30"])
            writer.writerow(["Bob", "25"])

        json_str = self.manager.convert(source_file, "json")
        data = json.loads(json_str)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        self.assertEqual(data[1]["age"], "25") # CSV reads as strings

    def test_get_info(self):
        source_file = self.project_dir / "test.json"
        data = {"a": 1, "b": {"c": 2}}
        with open(source_file, "w") as f:
            json.dump(data, f)

        info = self.manager.get_info(source_file)
        self.assertEqual(info["keys"], 2)
        self.assertEqual(info["depth"], 2)
        self.assertTrue(info["size_bytes"] > 0)

    def test_validate_json_syntax(self):
        source_file = self.project_dir / "valid.json"
        with open(source_file, "w") as f:
            f.write('{"key": "value"}')

        result = self.manager.validate(source_file)
        self.assertTrue(result["valid"])

        invalid_file = self.project_dir / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write('{"key": "value"') # Missing closing brace

        result = self.manager.validate(invalid_file)
        self.assertFalse(result["valid"])
        self.assertIn("Validation failed", result["message"])

    def test_unsupported_format(self):
        source_file = self.project_dir / "test.txt"
        source_file.touch()
        with self.assertRaises(ValueError):
            self.manager.convert(source_file, "json")

class TestRunDataLab(unittest.TestCase):
    @patch("main.sys.exit")
    @patch("shared.tui.AgentTUI")
    def test_run_data_lab_tui(self, mock_agent_tui, mock_exit):
        args = MagicMock()
        args.action = "tui"
        args.project_dir = Path("/tmp")

        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app

        run_data_lab(args)

        mock_agent_tui.assert_called_once_with(project_dir=Path("/tmp"), start_tab="tab-datalab")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    unittest.main()
