import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os
import argparse
import json
import io

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_todos

class TestMainTodos(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.args = argparse.Namespace(
            project_dir=self.project_dir,
            tags=None,
            blame=False,
            json=False
        )

    @patch("shared.todos.scan_todos")
    def test_run_todos_no_items(self, mock_scan):
        mock_scan.return_value = []

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_todos(self.args)
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("No TODOs found", fake_out.getvalue())

    @patch("shared.todos.scan_todos")
    def test_run_todos_with_items(self, mock_scan):
        mock_scan.return_value = [
            {'file': 'test.py', 'line': 1, 'tag': 'TODO', 'text': 'Fix it', 'raw_content': '# TODO: Fix it'}
        ]

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_todos(self.args)
            self.assertEqual(cm.exception.code, 0)
            output = fake_out.getvalue()
            self.assertIn("test.py", output)
            self.assertIn("TODO", output)
            self.assertIn("Fix it", output)

    @patch("shared.todos.get_todo_blame")
    @patch("shared.todos.scan_todos")
    def test_run_todos_blame(self, mock_scan, mock_blame):
        self.args.blame = True
        mock_scan.return_value = [
            {'file': 'test.py', 'line': 1, 'tag': 'TODO', 'text': 'Fix it', 'raw_content': '# TODO: Fix it'}
        ]
        mock_blame.return_value = {'author': 'Alice', 'date': '2023-01-01', 'commit': 'abc'}

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_todos(self.args)
            self.assertEqual(cm.exception.code, 0)
            output = fake_out.getvalue()
            self.assertIn("Alice", output)
            self.assertIn("2023-01-01", output)

    @patch("shared.todos.scan_todos")
    def test_run_todos_json(self, mock_scan):
        self.args.json = True
        mock_scan.return_value = [
            {'file': 'test.py', 'line': 1, 'tag': 'TODO', 'text': 'Fix it'}
        ]

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_todos(self.args)
            self.assertEqual(cm.exception.code, 0)
            output = fake_out.getvalue()
            data = json.loads(output)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['file'], 'test.py')

if __name__ == '__main__':
    unittest.main()
