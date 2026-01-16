import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import argparse
import os

# Ensure the shared module is in the path
# No, run_tests.sh handles PYTHONPATH
# sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.replay import run_replay, parse_log_file

class TestReplay(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and mock log files for testing."""
        self.test_dir = Path("./test_project_replay").resolve()
        self.test_dir.mkdir(exist_ok=True)

        self.history_file = self.test_dir / ".agent_history"
        self.history_file.write_text("test_run_1\ntest_run_2\n")

        # The replay logic calculates the repo root from its own file path,
        # so we need to create the mock logs relative to that.
        self.repo_root = Path(__file__).parent.parent
        self.logs_dir = self.repo_root / "agents/logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.log_file_1 = self.logs_dir / "test_run_1.log"
        self.log_file_1.write_text("2023-01-01 12:00:00,000 - INFO - Event 1\nLine 2 of event 1\n")

        self.log_file_2 = self.logs_dir / "test_run_2.log"
        self.log_file_2.write_text("2023-01-01 12:01:00,000 - INFO - Event A\n2023-01-01 12:02:00,000 - DEBUG - Event B\n2023-01-01 12:03:00,000 - ERROR - Event C\n")

    def tearDown(self):
        """Clean up the temporary directory and mock log files."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        if self.logs_dir.exists():
            shutil.rmtree(self.logs_dir)

    def test_parse_log_file(self):
        """Test that the log file is parsed into distinct events correctly."""
        events = parse_log_file(self.log_file_2)
        self.assertEqual(len(events), 3)
        self.assertIn("Event A", events[0])
        self.assertIn("Event B", events[1])
        self.assertIn("Event C", events[2])

    def test_parse_multiline_log_entry(self):
        """Test that multi-line log entries are parsed as a single event."""
        events = parse_log_file(self.log_file_1)
        self.assertEqual(len(events), 1)
        self.assertIn("Event 1\nLine 2 of event 1", events[0])

    @patch('builtins.input', side_effect=['n', 'q'])
    @patch('shared.replay.display_event')
    def test_navigation_next_and_quit(self, mock_display_event, mock_input):
        """Test navigating forward and quitting."""
        args = argparse.Namespace(project_dir=self.test_dir, run_id="test_run_2")
        with self.assertRaises(SystemExit) as cm:
            run_replay(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_display_event.call_count, 2)
        # First call (initial display)
        self.assertIn("Event A", mock_display_event.call_args_list[0].args[0])
        self.assertEqual(1, mock_display_event.call_args_list[0].args[1]) # event_number
        # Second call (after 'n')
        self.assertIn("Event B", mock_display_event.call_args_list[1].args[0])
        self.assertEqual(2, mock_display_event.call_args_list[1].args[1])

    @patch('builtins.input', side_effect=['n', 'b', 'q'])
    @patch('shared.replay.display_event')
    def test_navigation_back(self, mock_display_event, mock_input):
        """Test navigating forward then backward."""
        args = argparse.Namespace(project_dir=self.test_dir, run_id="test_run_2")
        with self.assertRaises(SystemExit) as cm:
            run_replay(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_display_event.call_count, 3)
        # event 1
        self.assertIn("Event A", mock_display_event.call_args_list[0].args[0])
        # event 2 (after 'n')
        self.assertIn("Event B", mock_display_event.call_args_list[1].args[0])
        # event 1 again (after 'b')
        self.assertIn("Event A", mock_display_event.call_args_list[2].args[0])

    @patch('builtins.input', side_effect=['j', '3', 'q'])
    @patch('shared.replay.display_event')
    def test_navigation_jump(self, mock_display_event, mock_input):
        """Test jumping to a specific event."""
        args = argparse.Namespace(project_dir=self.test_dir, run_id="test_run_2")
        with self.assertRaises(SystemExit) as cm:
            run_replay(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(mock_display_event.call_count, 2)
        # Call 1 (initial)
        self.assertIn("Event A", mock_display_event.call_args_list[0].args[0])
        self.assertEqual(1, mock_display_event.call_args_list[0].args[1])
        # Call 2 (after jump)
        self.assertIn("Event C", mock_display_event.call_args_list[1].args[0])
        self.assertEqual(3, mock_display_event.call_args_list[1].args[1])

    @patch('builtins.input', side_effect=['q'])
    @patch('shared.replay.parse_log_file')
    def test_no_run_id_uses_latest(self, mock_parse, mock_input):
        """Test that omitting a run_id uses the latest run from history."""
        mock_parse.return_value = ["mock event"]
        args = argparse.Namespace(project_dir=self.test_dir, run_id=None)

        with self.assertRaises(SystemExit):
            run_replay(args)

        mock_parse.assert_called_once()
        # Check that the path passed to the parser was for the latest run
        log_path_arg = mock_parse.call_args[0][0]
        self.assertEqual(log_path_arg.name, "test_run_2.log")

if __name__ == '__main__':
    unittest.main()
