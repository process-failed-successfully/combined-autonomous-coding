import unittest
import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch
from shared.json2xml_lab import Json2XmlManager, run_json2xml_lab_logic


class TestJson2XmlLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2XmlManager()

    def test_convert_flat_json(self):
        json_data = '{"name": "Alice", "age": 30}'
        expected = "<root>\n  <name>Alice</name>\n  <age>30</age>\n</root>"
        result = self.manager.convert(json_data)
        self.assertEqual(result, expected)

    def test_convert_nested_json(self):
        json_data = '{"person": {"name": "Bob", "address": {"city": "New York"}}}'
        expected = "<person>\n  <name>Bob</name>\n  <address>\n    <city>New York</city>\n  </address>\n</person>"
        result = self.manager.convert(json_data)
        self.assertEqual(result, expected)

    def test_convert_list_of_dicts(self):
        json_data = '[{"name": "Alice"}, {"name": "Bob"}]'
        expected = "<root>\n  <item>\n    <name>Alice</name>\n  </item>\n  <item>\n    <name>Bob</name>\n  </item>\n</root>"
        result = self.manager.convert(json_data)
        self.assertEqual(result, expected)

    def test_convert_empty_json(self):
        json_data = '{}'
        result = self.manager.convert(json_data)
        self.assertEqual(result, "")

    def test_invalid_json(self):
        json_data = '{"name": "Alice"'
        with self.assertRaises(ValueError):
            self.manager.convert(json_data)

    @patch('builtins.print')
    def test_cli_logic_text(self, mock_print):
        args = argparse.Namespace(text='{"name": "Alice"}', file=None, output=None)
        success = run_json2xml_lab_logic(args)
        self.assertTrue(success)
        mock_print.assert_called()

    @patch('sys.stdin.isatty', return_value=True)
    @patch('sys.stderr.write')
    def test_cli_logic_missing_args(self, mock_stderr, mock_isatty):
        args = argparse.Namespace(text=None, file=None)
        success = run_json2xml_lab_logic(args)
        self.assertFalse(success)

    def test_process_file(self):
        json_data = '{"name": "Alice"}'
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(json_data)
            temp_path = Path(f.name)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xml') as out_f:
            out_path = Path(out_f.name)

        try:
            args = argparse.Namespace(file=str(temp_path), text=None, output=str(out_path))
            success = run_json2xml_lab_logic(args)
            self.assertTrue(success)

            with open(out_path, 'r') as r:
                result_xml = r.read().strip()
            # the convert method doesn't wrap with root if there is a single element
            self.assertEqual(result_xml, "<name>Alice</name>")
        finally:
            temp_path.unlink()
            out_path.unlink()


if __name__ == "__main__":
    unittest.main()
