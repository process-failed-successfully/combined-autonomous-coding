import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import argparse
import sys
from shared.jmespath_lab import run_jmespath_lab_logic

class TestJmesPathLabCli(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_jmespath_lab_logic_text(self, mock_stdout):
        args = argparse.Namespace(
            expression="locations[0].name",
            text='{"locations": [{"name": "Seattle"}]}',
            file=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Seattle", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_run_jmespath_lab_logic_missing_expr(self, mock_stderr):
        args = argparse.Namespace(expression=None)
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("--expression is required", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_run_jmespath_lab_logic_invalid_json_text(self, mock_stderr):
        args = argparse.Namespace(
            expression="locations",
            text='invalid json',
            file=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error parsing JSON text", mock_stderr.getvalue())

    @patch('builtins.open', new_callable=MagicMock)
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_jmespath_lab_logic_file(self, mock_stdout, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = '{"foo": "bar"}'
        args = argparse.Namespace(
            expression="foo",
            file="test.json",
            text=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("bar", mock_stdout.getvalue())

    @patch('builtins.open', side_effect=FileNotFoundError("Not found"))
    @patch('sys.stderr', new_callable=StringIO)
    def test_run_jmespath_lab_logic_missing_file(self, mock_stderr, mock_open):
        args = argparse.Namespace(
            expression="foo",
            file="missing.json",
            text=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error reading file missing.json", mock_stderr.getvalue())

    @patch('sys.stdin')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_jmespath_lab_logic_stdin(self, mock_stdout, mock_stdin):
        mock_stdin.isatty.return_value = False
        mock_stdin.read.return_value = '{"a": 1}'
        args = argparse.Namespace(
            expression="a",
            file=None,
            text=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("1", mock_stdout.getvalue())

    @patch('sys.stdin')
    @patch('sys.stderr', new_callable=StringIO)
    def test_run_jmespath_lab_logic_no_input(self, mock_stderr, mock_stdin):
        mock_stdin.isatty.return_value = True
        args = argparse.Namespace(
            expression="a",
            file=None,
            text=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Please provide JSON via --file, --text, or stdin", mock_stderr.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_run_jmespath_lab_logic_invalid_expr(self, mock_stderr):
        args = argparse.Namespace(
            expression="foo[",
            text='{"foo": "bar"}',
            file=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error evaluating JMESPath", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_jmespath_lab_logic_null_result(self, mock_stdout):
        args = argparse.Namespace(
            expression="missing",
            text='{"foo": "bar"}',
            file=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_jmespath_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("null", mock_stdout.getvalue())


    @patch('sys.stderr', new_callable=StringIO)
    def test_run_jmespath_lab_logic_stdin_error(self, mock_stderr):
        with patch('sys.stdin') as mock_stdin:
            mock_stdin.isatty.return_value = False
            mock_stdin.read.side_effect = Exception("Read error")
            args = argparse.Namespace(
                expression="a",
                file=None,
                text=None
            )
            with self.assertRaises(SystemExit) as cm:
                run_jmespath_lab_logic(args)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Error parsing JSON from stdin", mock_stderr.getvalue())
