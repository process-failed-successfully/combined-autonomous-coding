import unittest
import argparse
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.csv2json_lab import Csv2JsonManager, run_csv2json_lab_logic

class TestCsv2JsonLab(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2JsonManager()

    def test_convert_raw_string(self):
        csv_data = "name,age,city\nAlice,30,New York\nBob,25,London"
        expected = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "London"}
        ]
        result = self.manager.convert(csv_data)
        self.assertEqual(result, expected)

    def test_convert_with_custom_delimiter(self):
        csv_data = "name;age;city\nAlice;30;New York\nBob;25;London"
        expected = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "London"}
        ]
        result = self.manager.convert(csv_data, delimiter=";")
        self.assertEqual(result, expected)

    def test_process_file(self):
        csv_data = "name,age,city\nAlice,30,New York"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write(csv_data)
            temp_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as out_f:
            out_path = Path(out_f.name)

        try:
            success = self.manager.process_file(temp_path, out_path)
            self.assertTrue(success)

            with open(out_path, 'r') as r:
                result_json = json.load(r)
            self.assertEqual(result_json, [{"name": "Alice", "age": "30", "city": "New York"}])
        finally:
            temp_path.unlink()
            out_path.unlink()

    @patch('builtins.print')
    def test_cli_logic_text(self, mock_print):
        args = argparse.Namespace(text="name,age\nAlice,30", file=None, output=None, delimiter=",")
        success = run_csv2json_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called()

    @patch('sys.stderr.write')
    def test_cli_logic_missing_args(self, mock_stderr):
        args = argparse.Namespace(text=None, file=None)
        success = run_csv2json_lab_logic(args)
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
