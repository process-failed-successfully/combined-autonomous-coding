import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import time
import os

from main import run_watch, CommandEventHandler

class TestWatchCommand(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_watch_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "test_file.txt"
        self.test_file.write_text("initial content")

    def tearDown(self):
        os.remove(self.test_file)
        os.rmdir(self.test_dir)

    @patch('main.Observer')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    def test_run_watch_starts_and_stops_observer(self, mock_sleep, mock_observer):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.test_dir,
            watch_command=['ls']
        )
        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_watch(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_observer_instance.start.assert_called_once()
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()

    @patch('main.subprocess.run')
    def test_command_event_handler_runs_command_on_modification(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['pytest', 'tests/']
        resolved_test_dir = self.test_dir.resolve()
        event_handler = CommandEventHandler(command_to_run, resolved_test_dir)
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.test_file)

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_subprocess_run.assert_called_once_with(command_to_run, cwd=resolved_test_dir)

    @patch('main.subprocess.run')
    def test_command_event_handler_ignores_directories(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['pytest']
        resolved_test_dir = self.test_dir.resolve()
        event_handler = CommandEventHandler(command_to_run, resolved_test_dir)
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(self.test_dir)

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_subprocess_run.assert_not_called()

    @patch('main.Observer')
    @patch('main.subprocess.run')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    def test_run_watch_triggers_command_on_file_change(self, mock_sleep, mock_subprocess_run, mock_observer):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.test_dir,
            watch_command=['my-test-command']
        )
        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_watch(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        # Get the event handler that was scheduled with the observer
        event_handler = mock_observer_instance.schedule.call_args[0][0]

        # Create a mock event to simulate a file modification
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.test_file)

        # Manually trigger the event handler's on_modified method
        event_handler.on_modified(mock_event)

        # Check that the command was run
        mock_subprocess_run.assert_called_once_with(['my-test-command'], cwd=self.test_dir.resolve())

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_watch_exits_if_no_command_provided(self, mock_stderr):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.test_dir,
            watch_command=[]
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_watch(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("No command provided", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
