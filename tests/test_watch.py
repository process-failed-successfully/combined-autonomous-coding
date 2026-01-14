import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os
import time

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from main import run_watch, parse_args, CommandEventHandler

class TestWatchCommand(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = Path("test_watch_project")
        self.test_dir.mkdir(exist_ok=True)
        (self.test_dir / ".git").mkdir(exist_ok=True)
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('main.Observer')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    def test_watch_command_triggers(self, mock_sleep, mock_observer):
        """Test that the watch command sets up the observer and handler correctly."""
        # Mock the arguments for the watch command
        with patch('sys.argv', ['main.py', 'watch', 'echo', 'hello']):
            args = parse_args()

            # Mock the event handler and observer instances
            mock_instance = mock_observer.return_value

            with self.assertRaises(SystemExit) as cm:
                run_watch(args)
            self.assertEqual(cm.exception.code, 0)

            # Assert that the observer was scheduled with the correct handler and path
            mock_instance.schedule.assert_called_once()
            handler = mock_instance.schedule.call_args[0][0]
            self.assertEqual(handler.command, ['echo', 'hello'])
            self.assertEqual(handler.project_dir, Path('.').resolve())

    @patch('main.subprocess.run')
    @patch('main.time.sleep', return_value=None) # Patch sleep to avoid delays
    def test_event_handler_runs_command(self, mock_sleep, mock_subprocess_run):
        """Test that the event handler executes the command on file modification."""
        if not main.PatternMatchingEventHandler:
            self.skipTest("watchdog is not installed")

        handler = main.CommandEventHandler(command=['npm', 'test'], project_dir='.')

        # Simulate a file modification event
        mock_event = MagicMock()
        mock_event.src_path = 'test.py'
        mock_event.is_directory = False

        handler.on_modified(mock_event)

        # Allow time for debouncing if any
        time.sleep(0.1)

        mock_subprocess_run.assert_called_with(['npm', 'test'], cwd='.')

    @patch('main.subprocess.run')
    @patch('main.time.sleep', return_value=None)
    def test_clear_screen_option(self, mock_sleep, mock_subprocess_run):
        """Test the --clear functionality."""
        if not main.PatternMatchingEventHandler:
            self.skipTest("watchdog is not installed")

        handler = main.CommandEventHandler(command=['pytest'], project_dir='.', clear=True)

        mock_event = MagicMock()
        mock_event.src_path = 'test_math.py'
        mock_event.is_directory = False

        handler.on_modified(mock_event)
        time.sleep(0.1)

        # Assert that subprocess.run was called to clear the screen
        clear_command = 'cls' if os.name == 'nt' else 'clear'
        mock_subprocess_run.assert_any_call(clear_command, shell=True)
        mock_subprocess_run.assert_any_call(['pytest'], cwd='.')

    @patch('main.threading.Timer')
    @patch('main.subprocess.run')
    def test_debouncing_logic(self, mock_subprocess_run, mock_timer):
        """Test that debouncing prevents rapid command execution and runs once after the delay."""
        if not main.PatternMatchingEventHandler:
            self.skipTest("watchdog is not installed")

        handler = CommandEventHandler(command=['flake8'], project_dir='.', delay=0.1)
        # Pre-seed the last run time to isolate the debouncing logic
        handler.last_run_time = time.time()

        mock_event = MagicMock()
        mock_event.src_path = 'app.py'
        mock_event.is_directory = False

        # Simulate three events in quick succession
        handler.on_modified(mock_event)
        handler.on_modified(mock_event)
        handler.on_modified(mock_event)

        # The command should not be called immediately because we pre-seeded the time
        mock_subprocess_run.assert_not_called()

        # A timer should have been scheduled on the first call
        mock_timer.assert_called_once()

        # Manually execute the function that the timer would have called
        # call_args is a tuple of (positional_args, keyword_args)
        pos_args, kw_args = mock_timer.call_args
        function = pos_args[1]
        function_args = kw_args['args']
        function(*function_args)

        # Now the command should have been called exactly once
        mock_subprocess_run.assert_called_once()
        self.assertEqual(mock_subprocess_run.call_count, 1)

    @patch.object(CommandEventHandler, 'handle_event')
    def test_pattern_matching(self, mock_handle_event):
        """Test that the handler correctly matches file patterns."""
        if not main.PatternMatchingEventHandler:
            self.skipTest("watchdog is not installed")

        handler = CommandEventHandler(
            command=['test'],
            project_dir='.',
            patterns=["*.py", "*.js"],
            ignore_patterns=["*.tmp", "build/*"]
        )

        # Helper to create an event mock
        def create_event(path, event_type='modified'):
            event = MagicMock()
            event.src_path = path
            event.is_directory = False
            event.event_type = event_type
            return event

        # Positive cases
        handler.dispatch(create_event('test.py', 'created'))
        self.assertEqual(mock_handle_event.call_count, 1)

        handler.dispatch(create_event('src/app.js', 'modified'))
        self.assertEqual(mock_handle_event.call_count, 2)

        # Negative cases
        handler.dispatch(create_event('test.txt', 'created'))
        handler.dispatch(create_event('test.py.tmp', 'modified'))
        handler.dispatch(create_event('build/output.js', 'created'))
        self.assertEqual(mock_handle_event.call_count, 2)

if __name__ == '__main__':
    unittest.main()
