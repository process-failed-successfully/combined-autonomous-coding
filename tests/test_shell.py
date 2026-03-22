import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from pathlib import Path

# Mock the main module and its functions that the shell will call
mock_main = MagicMock()
mock_main._run_status_logic = MagicMock()
mock_main._run_logs_logic = MagicMock()
mock_main._run_summary_logic = MagicMock()
mock_main._run_history_logic = MagicMock()
mock_main._run_diff_summary_logic = MagicMock()

# Since the shell imports main, we need to make sure the mock is in place
# before the shell module is imported.
sys.modules['__main__'] = mock_main

from shared.shell import InteractiveShell

class TestInteractiveShell(unittest.TestCase):

    def setUp(self):
        """Set up for each test."""
        self.shell = InteractiveShell(mock_main)
        # Redirect stdout to capture output from the shell commands
        self.mock_stdout = io.StringIO()
        self.stdout_backup = sys.stdout
        sys.stdout = self.mock_stdout

    def tearDown(self):
        """Clean up after each test."""
        sys.stdout = self.stdout_backup
        # Clear mocks for test isolation
        mock_main.reset_mock()

    def test_do_exit(self):
        """Test the exit command."""
        self.assertTrue(self.shell.onecmd("exit"))
        self.assertIn("Exiting.", self.mock_stdout.getvalue())

    def test_do_quit(self):
        """Test the quit command."""
        self.assertTrue(self.shell.onecmd("quit"))

    def test_do_EOF(self):
        """Test Ctrl+D (EOF)."""
        self.assertTrue(self.shell.onecmd("EOF"))

    def test_emptyline(self):
        """Test that an empty line does nothing."""
        self.shell.onecmd("")
        self.assertEqual(self.mock_stdout.getvalue(), "")

    def test_do_status(self):
        """Test the status command."""
        self.shell.onecmd("status")
        mock_main._run_status_logic.assert_called_once_with(project_dir='.')

    def test_do_status_with_project_dir(self):
        """Test the status command with a project directory."""
        self.shell.onecmd("status -p /tmp/project")
        mock_main._run_status_logic.assert_called_once_with(project_dir='/tmp/project')

    def test_do_logs(self):
        """Test the logs command without a run_id."""
        self.shell.onecmd("logs")
        mock_main._run_logs_logic.assert_called_once_with(run_id=None)

    def test_do_logs_with_run_id(self):
        """Test the logs command with a run_id."""
        self.shell.onecmd("logs 12345")
        mock_main._run_logs_logic.assert_called_once_with(run_id='12345')

    def test_do_summary(self):
        """Test the summary command."""
        self.shell.onecmd("summary")
        mock_main._run_summary_logic.assert_called_once_with(project_dir='.')

    def test_do_history(self):
        """Test the history command."""
        self.shell.onecmd("history")
        mock_main._run_history_logic.assert_called_once_with(project_dir='.')

    def test_do_diff_summary(self):
        """Test the diff-summary command."""
        self.shell.onecmd("diff_summary")
        mock_main._run_diff_summary_logic.assert_called_once_with(project_dir='.')

    @patch('subprocess.run')
    def test_default_command(self, mock_run):
        """Test that unrecognized commands are passed to the system shell."""
        self.shell.onecmd("ls -la")
        mock_run.assert_called_once_with("ls -la", shell=True, check=False)

    @patch('subprocess.run')
    def test_default_command_exception(self, mock_run):
        """Test that exceptions from subprocess.run are caught and printed."""
        mock_run.side_effect = Exception("Test exception")
        self.shell.onecmd("failing_command")
        self.assertIn("Error executing command: Test exception", self.mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
