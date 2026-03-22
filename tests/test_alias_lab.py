import unittest
from unittest.mock import patch
import sys
from pathlib import Path
from shared.alias_lab import run_alias_lab_logic

class DummyArgs:
    def __init__(self, shell="bash", prefix=""):
        self.shell = shell
        self.prefix = prefix

class TestAliasLab(unittest.TestCase):

    @patch("sys.stdout")
    def test_run_alias_lab_bash(self, mock_stdout):
        # We need to capture the printed output.
        import io
        fake_out = io.StringIO()
        with patch('sys.stdout', new=fake_out):
            known_commands = ["testcmd", "anothercmd"]
            args = DummyArgs(shell="bash", prefix="")
            success = run_alias_lab_logic(args, known_commands)

            self.assertTrue(success)
            output = fake_out.getvalue()
            main_py_path = Path(sys.argv[0]).resolve()

            self.assertIn("# Aliases generated for bash", output)
            self.assertIn(f"alias testcmd='\"{main_py_path}\" testcmd'", output)
            self.assertIn(f"alias anothercmd='\"{main_py_path}\" anothercmd'", output)

    @patch("sys.stdout")
    def test_run_alias_lab_fish_with_prefix(self, mock_stdout):
        import io
        fake_out = io.StringIO()
        with patch('sys.stdout', new=fake_out):
            known_commands = ["hello", "world"]
            args = DummyArgs(shell="fish", prefix="ag-")
            success = run_alias_lab_logic(args, known_commands)

            self.assertTrue(success)
            output = fake_out.getvalue()
            main_py_path = Path(sys.argv[0]).resolve()

            self.assertIn("# Aliases generated for fish", output)
            self.assertIn("# Prefix used: 'ag-'", output)
            self.assertIn(f"alias ag-hello '\"{main_py_path}\" hello'", output)
            self.assertIn(f"alias ag-world '\"{main_py_path}\" world'", output)

    @patch("sys.stderr")
    def test_run_alias_lab_unsupported_shell(self, mock_stderr):
        import io
        fake_err = io.StringIO()
        with patch('sys.stderr', new=fake_err):
            known_commands = ["cmd"]
            args = DummyArgs(shell="cmdexe", prefix="")
            success = run_alias_lab_logic(args, known_commands)

            self.assertFalse(success)
            err_output = fake_err.getvalue()
            self.assertIn("Unsupported shell 'cmdexe'", err_output)

    @patch("sys.stderr")
    def test_run_alias_lab_empty_commands(self, mock_stderr):
        import io
        fake_err = io.StringIO()
        with patch('sys.stderr', new=fake_err):
            known_commands = []
            args = DummyArgs(shell="bash", prefix="")
            success = run_alias_lab_logic(args, known_commands)

            self.assertTrue(success)
            err_output = fake_err.getvalue()
            self.assertIn("No commands found to alias.", err_output)

if __name__ == "__main__":
    unittest.main()
