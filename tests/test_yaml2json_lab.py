import unittest
import argparse
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.yaml2json_lab import Yaml2JsonManager, run_yaml2json_lab_logic

class TestYaml2JsonLab(unittest.TestCase):
    def setUp(self):
        self.manager = Yaml2JsonManager()

    def test_convert_raw_string(self):
        yaml_data = "name: Alice\nage: 30\ncity: New York\n"
        expected = {"name": "Alice", "age": 30, "city": "New York"}
        result = self.manager.convert(yaml_data)
        self.assertEqual(result, expected)

    def test_convert_invalid_yaml(self):
        # Invalid YAML due to bad indentation
        yaml_data = "name: Alice\n  age: 30"
        with self.assertRaises(ValueError):
            self.manager.convert(yaml_data)

    def test_process_file(self):
        yaml_data = "name: Alice\nage: 30\n"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
            f.write(yaml_data)
            temp_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as out_f:
            out_path = Path(out_f.name)

        try:
            success = self.manager.process_file(temp_path, out_path)
            self.assertTrue(success)

            with open(out_path, 'r') as r:
                result_json = json.load(r)
            self.assertEqual(result_json, {"name": "Alice", "age": 30})
        finally:
            temp_path.unlink()
            out_path.unlink()

    @patch('builtins.print')
    def test_cli_logic_text(self, mock_print):
        args = argparse.Namespace(text="name: Alice", file=None, output=None)
        success = run_yaml2json_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called()

    @patch('sys.stderr.write')
    def test_cli_logic_missing_args(self, mock_stderr):
        args = argparse.Namespace(text=None, file=None)
        success = run_yaml2json_lab_logic(args)
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
