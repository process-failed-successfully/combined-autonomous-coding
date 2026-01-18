import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os
import argparse
import io
import re

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # noqa: E402

from main import run_search

class TestMainSearch(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_search_project")
        self.args = argparse.Namespace(
            project_dir=self.project_dir,
            pattern="foo",
            files=None,
            case_sensitive=False,
            regex=False,
            context=0
        )

    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    @patch("shared.search.search_codebase")
    def test_run_search_no_items(self, mock_search):
        mock_search.return_value = []

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_search(self.args)
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("No matches found", fake_out.getvalue())

    @patch("shared.search.search_codebase")
    def test_run_search_with_items(self, mock_search):
        mock_search.return_value = [
            {
                'file': 'test.py',
                'line': 10,
                'content': 'foo bar',
                'context_before': [],
                'context_after': []
            }
        ]

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_search(self.args)
            self.assertEqual(cm.exception.code, 0)
            output = self.strip_ansi(fake_out.getvalue())
            self.assertIn("test.py", output)
            self.assertIn("10: foo bar", output)
            self.assertIn("Found 1 matches", output)

    @patch("shared.search.search_codebase")
    def test_run_search_with_context(self, mock_search):
        self.args.context = 1
        mock_search.return_value = [
            {
                'file': 'test.py',
                'line': 10,
                'content': 'foo bar',
                'context_before': ['9: prev'],
                'context_after': ['11: next']
            }
        ]

        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                run_search(self.args)
            self.assertEqual(cm.exception.code, 0)
            output = self.strip_ansi(fake_out.getvalue())
            self.assertIn("9: prev", output)
            self.assertIn("11: next", output)

if __name__ == '__main__':
    unittest.main()
