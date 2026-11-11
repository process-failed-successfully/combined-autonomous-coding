import unittest
import argparse
from unittest.mock import patch
import io
from shared.chmod_lab import ChmodLabManager, run_chmod_lab_logic

class TestChmodLab(unittest.TestCase):
    def test_parse_octal_755(self):
        result = ChmodLabManager.parse("755")
        self.assertEqual(result["octal"], "755")
        self.assertEqual(result["symbolic"], "rwxr-xr-x")
        self.assertEqual(result["binary"], "111101101")
        self.assertEqual(result["owner"], "read, write, execute")
        self.assertEqual(result["group"], "read, execute")
        self.assertEqual(result["public"], "read, execute")

    def test_parse_octal_0755(self):
        result = ChmodLabManager.parse("0755")
        self.assertEqual(result["octal"], "755")

    def test_parse_symbolic_9chars(self):
        result = ChmodLabManager.parse("rwxr-xr-x")
        self.assertEqual(result["octal"], "755")
        self.assertEqual(result["symbolic"], "rwxr-xr-x")
        self.assertEqual(result["binary"], "111101101")

    def test_parse_symbolic_10chars(self):
        result = ChmodLabManager.parse("-rwxr-xr-x")
        self.assertEqual(result["octal"], "755")
        self.assertEqual(result["symbolic"], "rwxr-xr-x")

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            ChmodLabManager.parse("invalid")
        with self.assertRaises(ValueError):
            ChmodLabManager.parse("77")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_run_logic(self, mock_stdout):
        args = argparse.Namespace(permission="755", tui=False)
        self.assertTrue(run_chmod_lab_logic(args))
        output = mock_stdout.getvalue()
        self.assertIn("Octal:    755", output)
        self.assertIn("Symbolic: rwxr-xr-x", output)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_run_logic_no_args(self, mock_stderr):
        args = argparse.Namespace(permission=None, tui=False)
        self.assertFalse(run_chmod_lab_logic(args))
        self.assertIn("must provide a permission string or --tui", mock_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
