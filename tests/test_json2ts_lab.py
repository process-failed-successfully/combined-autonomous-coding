import unittest
import argparse
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from shared.json2ts_lab import Json2TsManager, run_json2ts_lab_logic

class TestJson2TsLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2TsManager()

    def test_simple_object(self):
        json_str = '{"name": "Alice", "age": 30, "isActive": true}'
        expected = """export interface Root {
  name: string;
  age: number;
  isActive: boolean;
}"""
        self.assertEqual(self.manager.convert(json_str).strip(), expected)

    def test_nested_object(self):
        json_str = '{"id": 1, "address": {"city": "Paris", "zip": "75001"}}'
        result = self.manager.convert(json_str).strip()
        self.assertIn("export interface Address", result)
        self.assertIn("city: string;", result)
        self.assertIn("export interface Root", result)
        self.assertIn("address: Address;", result)

    def test_array_of_objects(self):
        json_str = '[{"role": "admin"}]'
        result = self.manager.convert(json_str).strip()
        self.assertIn("export interface Root", result)
        self.assertIn("role: string;", result)

    def test_arrays_in_object(self):
        json_str = '{"tags": ["a", "b"], "scores": [1, 2], "empty": []}'
        expected = """export interface Root {
  tags: string[];
  scores: number[];
  empty: any[];
}"""
        self.assertEqual(self.manager.convert(json_str).strip(), expected)

    def test_array_of_objects_property(self):
        json_str = '{"items": [{"id": 1}]}'
        result = self.manager.convert(json_str).strip()
        self.assertIn("export interface Items", result)
        self.assertIn("export interface Root", result)
        self.assertIn("items: Items[];", result)

    def test_empty_string(self):
        self.assertEqual(self.manager.convert(""), "")

    def test_invalid_json(self):
        result = self.manager.convert("{invalid json}")
        self.assertTrue(result.startswith("Error parsing JSON:"))

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_text(self, mock_stdout):
        args = argparse.Namespace(text='{"ok": true}', file=None, output=None, name="Root", tui=False)
        result = run_json2ts_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("export interface Root", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('pathlib.Path.write_text')
    def test_run_logic_output_file(self, mock_write, mock_stdout):
        args = argparse.Namespace(text='{"x": 1}', file=None, output='out.ts', name="Root", tui=False)
        result = run_json2ts_lab_logic(args)
        self.assertTrue(result)
        mock_write.assert_called_once()
        self.assertIn("Saved TS to out.ts", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_run_logic_no_input(self, mock_stderr):
        args = argparse.Namespace(text=None, file=None, output=None, name="Root", tui=False)
        with patch('sys.stdin.isatty', return_value=True):
            result = run_json2ts_lab_logic(args)
            self.assertFalse(result)
            self.assertIn("Input required", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stdin.read', return_value='{"from_stdin": true}')
    def test_run_logic_stdin(self, mock_stdin_read, mock_stdout):
        args = argparse.Namespace(text=None, file=None, output=None, name="Root", tui=False)
        with patch('sys.stdin.isatty', return_value=False):
            result = run_json2ts_lab_logic(args)
            self.assertTrue(result)
            self.assertIn("export interface Root", mock_stdout.getvalue())
            self.assertIn('"from_stdin": boolean;', mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
