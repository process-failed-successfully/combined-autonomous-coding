import unittest
import argparse
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.json2yaml_lab import Json2YamlManager, run_json2yaml_lab_logic

class TestJson2YamlLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2YamlManager()

    def test_convert_raw_string(self):
        json_data = '{"name": "Alice", "age": 30, "city": "New York"}'
        result = self.manager.convert(json_data)
        data = yaml.safe_load(result)
        self.assertEqual(data, {"name": "Alice", "age": 30, "city": "New York"})

    def test_convert_invalid_json(self):
        # Invalid JSON due to missing quotes
        json_data = '{name: "Alice", "age": 30}'
        with self.assertRaises(ValueError):
            self.manager.convert(json_data)

    def test_process_file(self):
        json_data = '{"name": "Alice", "age": 30}'
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(json_data)
            temp_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as out_f:
            out_path = Path(out_f.name)

        try:
            success = self.manager.process_file(temp_path, out_path)
            self.assertTrue(success)

            with open(out_path, 'r') as r:
                result_yaml = yaml.safe_load(r)
            self.assertEqual(result_yaml, {"name": "Alice", "age": 30})
        finally:
            temp_path.unlink()
            out_path.unlink()

    @patch('builtins.print')
    def test_cli_logic_text(self, mock_print):
        args = argparse.Namespace(text='{"name": "Alice"}', file=None, output=None)
        success = run_json2yaml_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called()

    @patch('sys.stderr.write')
    def test_cli_logic_missing_args(self, mock_stderr):
        args = argparse.Namespace(text=None, file=None)
        success = run_json2yaml_lab_logic(args)
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
