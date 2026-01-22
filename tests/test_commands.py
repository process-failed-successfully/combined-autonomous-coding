from shared.commands import run_why
import unittest
from unittest.mock import patch
import io
import sys
from argparse import Namespace

# Add the project root to the path to allow imports from shared
sys.path.insert(0, sys.path[0] + "/..")


class TestWhyCommand(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_why_with_valid_command(self, mock_stdout):
        args = Namespace(command_name="status")
        with self.assertRaises(SystemExit) as cm:
            run_why(args)
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- What is `status`? ---", output)
        self.assertIn("Use this to get a detailed, color-coded dashboard", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_why_with_invalid_command(self, mock_stdout):
        args = Namespace(command_name="nonexistentcommand")
        with self.assertRaises(SystemExit) as cm:
            run_why(args)
        self.assertEqual(cm.exception.code, 1)
        output = mock_stdout.getvalue()
        self.assertIn("❌ Error: Command 'nonexistentcommand' not found", output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_why_with_no_command(self, mock_stdout):
        args = Namespace(command_name=None)
        with self.assertRaises(SystemExit) as cm:
            run_why(args)
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("--- Why, oh why? ---", output)
        self.assertIn("Usage: why <command_name>", output)
        self.assertIn("--- Available Commands ---", output)
        self.assertIn("status", output)
        self.assertIn("discard", output)


if __name__ == '__main__':
    unittest.main()
