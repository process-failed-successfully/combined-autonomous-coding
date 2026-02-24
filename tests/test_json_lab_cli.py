import unittest
from unittest.mock import MagicMock, patch
import sys
import io
import json
from shared.json_lab import run_json_lab_logic

class TestJsonLabCLI(unittest.TestCase):
    def setUp(self):
        self.mock_args = MagicMock()
        # Mock sys.stdout
        self.held, sys.stdout = sys.stdout, io.StringIO()
        self.held_stderr, sys.stderr = sys.stderr, io.StringIO()

    def tearDown(self):
        sys.stdout = self.held
        sys.stderr = self.held_stderr

    def test_query_action(self):
        data = {"items": [{"id": 1, "val": 10}, {"id": 2, "val": 20}]}
        json_str = json.dumps(data)

        self.mock_args.action = "query"
        self.mock_args.input = json_str
        self.mock_args.path = "[item['id'] for item in data['items'] if item['val'] > 15]"

        # Should NOT raise SystemExit
        run_json_lab_logic(self.mock_args)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, "[\n  2\n]")

    def test_query_action_error(self):
        self.mock_args.action = "query"
        self.mock_args.input = '{"a": 1}'
        self.mock_args.path = "1 / 0" # ZeroDivisionError

        with self.assertRaises(SystemExit) as cm:
            run_json_lab_logic(self.mock_args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error:", sys.stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
