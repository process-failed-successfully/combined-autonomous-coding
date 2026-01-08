import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import asyncio

# Create a mock for the main module. This needs to be done before importing the shell.
mock_main = MagicMock()

# This is a stand-in for the real get_parser() in main.py
def get_parser_mock():
    import argparse
    parser = argparse.ArgumentParser(prog="main.py", add_help=False)
    subparsers = parser.add_subparsers(dest="command")

    # Mock 'status' command
    parser_status = subparsers.add_parser("status")
    parser_status.add_argument("-p", "--project-dir", default=".")

    # Mock 'log' command
    parser_log = subparsers.add_parser("log")
    parser_log.add_argument("-n", "--count", type=int)
    parser_log.add_argument("-p", "--project-dir", default=".")

    # Mock 'plan' command (async)
    parser_plan = subparsers.add_parser("plan")
    parser_plan.add_argument("-s", "--spec")

    # Mock a command that will fail
    subparsers.add_parser("fail_command")

    return parser

mock_main.get_parser = get_parser_mock
mock_main._run_status_logic = MagicMock(return_value=0)
mock_main._run_log_logic = MagicMock(return_value=0)
mock_main._run_fail_command_logic = MagicMock(side_effect=Exception("Test failure"))

# We also need a mock for the async 'plan' command
async_plan_mock = MagicMock()
async def mock_plan_logic(args):
    async_plan_mock(args)
    return 0
mock_main._run_plan_logic = mock_plan_logic

# Now, we can import the shell
from shared.shell import InteractiveShell

class TestInteractiveShell(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        # Reset mocks before each test
        mock_main.reset_mock()
        async_plan_mock.reset_mock()

        # Patch asyncio.run to run the coroutine directly.
        # This simplifies testing async functions called from the shell.
        self.run_patcher = patch('asyncio.run', new=lambda coro: asyncio.get_event_loop().run_until_complete(coro))
        self.run_patcher.start()

        self.shell = InteractiveShell(mock_main)
        self.mock_stdout = io.StringIO()
        self.stdout_backup = sys.stdout
        sys.stdout = self.mock_stdout

    def tearDown(self):
        """Clean up after each test."""
        self.run_patcher.stop()
        sys.stdout = self.stdout_backup

    def test_exit_commands(self):
        """Test that exit, quit, and EOF terminate the shell."""
        for cmd in ['exit', 'quit', 'EOF']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.shell.onecmd(cmd))
                self.assertIn("Exiting.", self.mock_stdout.getvalue())
                self.mock_stdout.truncate(0)
                self.mock_stdout.seek(0)

    def test_empty_line(self):
        """Test that an empty line does nothing."""
        self.shell.onecmd("")
        self.assertEqual(self.mock_stdout.getvalue(), "")

    def test_dispatch_simple_command(self):
        """Test dispatching a simple command like 'status'."""
        self.shell.onecmd("status")
        mock_main._run_status_logic.assert_called_once()
        args, _ = mock_main._run_status_logic.call_args
        self.assertEqual(args[0].command, "status")
        self.assertEqual(args[0].project_dir, ".")

    def test_dispatch_with_arguments(self):
        """Test a command with arguments, like 'log -n 10'."""
        self.shell.onecmd("log -n 10")
        mock_main._run_log_logic.assert_called_once()
        args, _ = mock_main._run_log_logic.call_args
        self.assertEqual(args[0].command, "log")
        self.assertEqual(args[0].count, 10)

    def test_dispatch_async_command(self):
        """Test that async functions are correctly awaited."""
        self.shell.onecmd("plan --spec /path/to/spec.txt")
        async_plan_mock.assert_called_once()
        args, _ = async_plan_mock.call_args
        self.assertEqual(args[0].command, "plan")
        self.assertEqual(args[0].spec, "/path/to/spec.txt")

    def test_unknown_command(self):
        """Test that an unknown command prints an error but doesn't exit."""
        self.shell.onecmd("this_is_not_a_real_command")
        # Argparse will print an error to stderr, which we are not capturing,
        # but we can check that no logic function was called.
        mock_main._run_status_logic.assert_not_called()
        mock_main._run_log_logic.assert_not_called()

    def test_command_raising_exception(self):
        """Test that the shell handles commands that raise exceptions gracefully."""
        # We need to add the 'fail_command' to the mock parser's logic map for the shell
        mock_main.command_map = {"fail_command": mock_main._run_fail_command_logic}
        self.shell.onecmd("fail_command")
        self.assertIn("*** Error: Test failure", self.mock_stdout.getvalue())
        # Make sure our logic function was actually called
        mock_main._run_fail_command_logic.assert_called_once()

if __name__ == '__main__':
    unittest.main()
