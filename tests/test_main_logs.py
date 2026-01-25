import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path
import tempfile
import time

# Add the parent directory to the sys.path to allow for absolute imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import _run_logs_logic

class TestLogsCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and fake log files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        self.logs_dir = self.repo_root / "agents" / "logs"
        self.logs_dir.mkdir(parents=True)

        # Create dummy log files
        self.log_content_1 = [
            "INFO - Starting process\n",
            "DEBUG - Step 1: Initialization\n",
            "INFO - Connecting to database\n",
            "WARNING - Weak password detected\n",
            "ERROR - Connection failed\n",
            "INFO - Retrying...\n",
        ]
        self.log_file_1 = self.logs_dir / "run_123.log"
        self.log_file_1.write_text("".join(self.log_content_1))

        time.sleep(0.01) # Ensure timestamps are different

        self.log_content_2 = [
            "INFO - Application started\n",
            "DEBUG - Loading configuration\n",
            "INFO - All systems nominal\n",
            "DEBUG - Checking for updates\n",
        ]
        self.log_file_2 = self.logs_dir / "run_456.log" # This one is newer
        self.log_file_2.write_text("".join(self.log_content_2))

    def tearDown(self):
        """Clean up the temporary directory."""
        self.temp_dir.cleanup()

    @patch('main.Path')
    def test_list_logs_no_id(self, mock_path):
        """Test listing logs when no run_id or flags are provided."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = _run_logs_logic()

        self.assertTrue(result)
        output = captured_output.getvalue()
        self.assertIn("--- Last 10 Agent Logs ---", output)
        self.assertIn("run_456 (latest)", output)
        self.assertIn("run_123", output)

    @patch('main.Path')
    def test_view_specific_log(self, mock_path):
        """Test viewing a whole specific log file."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = _run_logs_logic(run_id="run_123")

        self.assertTrue(result)
        output = captured_output.getvalue()
        self.assertIn("--- Displaying logs for: run_123.log ---", output)
        self.assertIn("ERROR - Connection failed", output)
        # +1 for the header line printed
        self.assertEqual(output.count('\n'), len(self.log_content_1) + 1)

    @patch('main.Path')
    def test_line_limit(self, mock_path):
        """Test the --lines flag to limit output."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = _run_logs_logic(run_id="run_123", lines=3)

        self.assertTrue(result)
        output = captured_output.getvalue()
        # Should contain the last 3 lines
        self.assertIn("WARNING - Weak password detected", output)
        self.assertIn("ERROR - Connection failed", output)
        self.assertIn("INFO - Retrying...", output)
        # Should not contain earlier lines
        self.assertNotIn("INFO - Starting process", output)
        self.assertEqual(output.count('\n'), 3 + 1)

    @patch('main.Path')
    def test_grep_filter(self, mock_path):
        """Test the --grep flag to filter output."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = _run_logs_logic(run_id="run_123", grep="INFO")

        self.assertTrue(result)
        output = captured_output.getvalue()
        # Should only contain lines with "INFO"
        self.assertIn("INFO - Starting process", output)
        self.assertIn("INFO - Connecting to database", output)
        self.assertIn("INFO - Retrying...", output)
        # Should not contain other lines
        self.assertNotIn("DEBUG", output)
        self.assertNotIn("WARNING", output)
        self.assertNotIn("ERROR", output)
        self.assertEqual(output.count('\n'), 3 + 1)

    @patch('main.Path')
    def test_lines_and_grep_combined(self, mock_path):
        """Test combining --lines and --grep."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
             result = _run_logs_logic(run_id="run_123", lines=4, grep="INFO")

        self.assertTrue(result)
        output = captured_output.getvalue()
        # From the last 4 lines of the log, 2 contain "INFO"
        self.assertIn("INFO - Retrying...", output)
        self.assertIn("INFO - Connecting to database", output)
        self.assertNotIn("INFO - Starting process", output)
        self.assertEqual(output.count('\n'), 2 + 1)

    @patch('main.Path')
    def test_lines_on_latest_log(self, mock_path):
        """Test using --lines without a run_id targets the latest log."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = _run_logs_logic(lines=2)

        self.assertTrue(result)
        output = captured_output.getvalue()
        self.assertIn("--- Displaying logs for: run_456.log ---", output)
        # Should have the last 2 lines of the newest log
        self.assertIn("INFO - All systems nominal", output)
        self.assertIn("DEBUG - Checking for updates", output)
        self.assertEqual(output.count('\n'), 2 + 1)

    @patch('main.Path')
    def test_log_not_found(self, mock_path):
        """Test correct handling of a non-existent log file."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            result = _run_logs_logic(run_id="non_existent_run")

        self.assertFalse(result)
        self.assertIn("Log file not found for Run ID: non_existent_run", captured_output.getvalue())

    @patch('time.sleep', side_effect=KeyboardInterrupt)
    @patch('main.Path')
    def test_follow_mode_interrupt(self, mock_path, mock_sleep):
        """Test that --follow mode can be interrupted."""
        mock_path.return_value.parent = self.repo_root

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            # Also use --lines to ensure initial content is printed before follow loop
            result = _run_logs_logic(run_id="run_123", follow=True, lines=10)

        self.assertTrue(result)
        output = captured_output.getvalue()
        # Check that it printed the initial content
        self.assertIn("ERROR - Connection failed", output)
        # Check that it printed the exit message
        self.assertIn("--- Stopped following log ---", output)

    @patch('sys.exit')
    def test_explore_flag(self, mock_exit):
        """Test that --explore flag prints a message and exits."""
        # args needs explore=True
        from main import run_logs
        args = MagicMock()
        args.explore = True
        args.project_dir = Path(".")
        args.agent = "gemini"

        # Make sys.exit raise SystemExit so execution stops
        mock_exit.side_effect = SystemExit

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            with self.assertRaises(SystemExit):
                run_logs(args)

        self.assertIn("Log Explorer is now integrated into the main TUI", captured_output.getvalue())
        mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()
