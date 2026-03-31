import unittest
from unittest.mock import MagicMock, patch
import io
import json
from shared.json_schema_lab import run_json_schema_lab_logic, JsonSchemaManager


class TestJsonSchemaLab(unittest.TestCase):
    def test_manager_generate(self):
        manager = JsonSchemaManager()
        data = {"name": "Test", "age": 30, "is_active": True, "tags": ["a", "b"]}
        schema = manager.generate(data)

        self.assertEqual(schema["$schema"], "http://json-schema.org/draft-07/schema#")
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["name"]["type"], "string")
        self.assertEqual(schema["properties"]["age"]["type"], "integer")
        self.assertEqual(schema["properties"]["is_active"]["type"], "boolean")
        self.assertEqual(schema["properties"]["tags"]["type"], "array")
        self.assertEqual(schema["properties"]["tags"]["items"]["type"], "string")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_logic_json_arg(self, mock_stdout):
        args = MagicMock()
        args.json = '{"name": "John"}'
        args.file = None
        args.output = None
        args.tui = False
        args.action = "generate"

        result = run_json_schema_lab_logic(args)
        self.assertTrue(result)

        output = mock_stdout.getvalue().strip()
        schema = json.loads(output)
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["name"]["type"], "string")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_logic_invalid_json(self, mock_stderr):
        args = MagicMock()
        args.json = '{"name": "John"'
        args.file = None
        args.output = None
        args.tui = False
        args.action = "generate"

        result = run_json_schema_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error parsing JSON", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_logic_no_input(self, mock_stderr):
        args = MagicMock()
        args.json = None
        args.file = None
        args.output = None
        args.tui = False
        args.action = "generate"

        with patch('sys.stdin.isatty', return_value=True):
            result = run_json_schema_lab_logic(args)
            self.assertFalse(result)
            self.assertIn("Please provide JSON", mock_stderr.getvalue())


if __name__ == '__main__':
    pass  # To avoid pytest complaining
