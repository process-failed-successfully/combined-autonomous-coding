import unittest
from unittest.mock import patch, MagicMock
import io
import os
import json
from pathlib import Path
from shared.json2toml_lab import Json2TomlManager, run_json2toml_lab_logic


class TestJson2TomlLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2TomlManager()

    def test_convert_json_to_toml_string(self):
        json_str = '{"name": "test", "value": 123}'
        expected_toml = 'name = "test"\nvalue = 123\n'
        result = self.manager.convert_json_to_toml(json_str)
        self.assertEqual(result, expected_toml)

    def test_convert_json_to_toml_invalid(self):
        with self.assertRaises(ValueError):
            self.manager.convert_json_to_toml('invalid json')

    def test_convert_json_to_toml_non_dict(self):
        with self.assertRaises(ValueError):
            self.manager.convert_json_to_toml('["a", "list"]')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_cli_logic_success(self, mock_stdout):
        args = MagicMock()
        args.action = "json2toml"
        args.input = '{"key": "value"}'
        args.output = None

        result = run_json2toml_lab_logic(args)

        self.assertTrue(result)
        self.assertEqual(mock_stdout.getvalue().strip(), 'key = "value"')

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_cli_logic_error(self, mock_stderr):
        args = MagicMock()
        args.action = "json2toml"
        args.input = 'invalid'
        args.output = None

        result = run_json2toml_lab_logic(args)

        self.assertFalse(result)
        self.assertIn("Error: Invalid JSON", mock_stderr.getvalue())

    def test_cli_logic_file_output(self):
        args = MagicMock()
        args.action = "json2toml"
        args.input = '{"file": "output"}'
        args.output = "test_output.toml"

        try:
            result = run_json2toml_lab_logic(args)
            self.assertTrue(result)
            with open(args.output, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, 'file = "output"\n')
        finally:
            if os.path.exists(args.output):
                os.remove(args.output)
