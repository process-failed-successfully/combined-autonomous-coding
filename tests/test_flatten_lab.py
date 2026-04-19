import unittest
from unittest.mock import MagicMock, patch
import json
import sys
from io import StringIO
from shared.flatten_lab import FlattenManager, run_flatten_lab_logic

class TestFlattenManager(unittest.TestCase):
    def setUp(self):
        self.manager = FlattenManager()

    def test_flatten_dict(self):
        nested = {"user": {"name": "Alice", "address": {"city": "Wonderland"}}}
        expected = {
            "user.name": "Alice",
            "user.address.city": "Wonderland"
        }
        self.assertEqual(self.manager.flatten(nested), expected)

    def test_flatten_list(self):
        nested = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        expected = {
            "users.0.name": "Alice",
            "users.1.name": "Bob"
        }
        self.assertEqual(self.manager.flatten(nested), expected)

    def test_flatten_empty(self):
        self.assertEqual(self.manager.flatten({}), {})
        self.assertEqual(self.manager.flatten([]), {})

    def test_flatten_mixed(self):
        nested = {"a": [1, {"b": 2}]}
        expected = {"a.0": 1, "a.1.b": 2}
        self.assertEqual(self.manager.flatten(nested), expected)

    def test_unflatten_dict(self):
        flat = {
            "user.name": "Alice",
            "user.address.city": "Wonderland"
        }
        expected = {"user": {"name": "Alice", "address": {"city": "Wonderland"}}}
        self.assertEqual(self.manager.unflatten(flat), expected)

    def test_unflatten_list(self):
        flat = {
            "users.0.name": "Alice",
            "users.1.name": "Bob"
        }
        expected = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        self.assertEqual(self.manager.unflatten(flat), expected)

    def test_flatten_custom_separator(self):
        manager = FlattenManager(separator="_")
        nested = {"a": {"b": 1}}
        expected = {"a_b": 1}
        self.assertEqual(manager.flatten(nested), expected)
        self.assertEqual(manager.unflatten(expected), nested)

class TestFlattenLabCLI(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_flatten_cli_text(self, mock_stdout):
        args = MagicMock()
        args.action = 'flatten'
        args.text = '{"a": {"b": 1}}'
        args.file = None
        args.output = None
        args.separator = '.'

        result = run_flatten_lab_logic(args)
        self.assertTrue(result)

        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output, {"a.b": 1})

    @patch('sys.stdout', new_callable=StringIO)
    def test_unflatten_cli_text(self, mock_stdout):
        args = MagicMock()
        args.action = 'unflatten'
        args.text = '{"a.b": 1}'
        args.file = None
        args.output = None
        args.separator = '.'

        result = run_flatten_lab_logic(args)
        self.assertTrue(result)

        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output, {"a": {"b": 1}})

    @patch('sys.stderr', new_callable=StringIO)
    def test_flatten_cli_invalid_json(self, mock_stderr):
        args = MagicMock()
        args.action = 'flatten'
        args.text = '{"a": 1'
        args.file = None
        args.output = None
        args.separator = '.'

        result = run_flatten_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error parsing JSON", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
