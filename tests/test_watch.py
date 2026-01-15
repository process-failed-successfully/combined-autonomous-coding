
import unittest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile
import time
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.watch_handler import CommandEventHandler, start_watcher

class TestWatchHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('subprocess.run')
    def test_command_event_handler_runs_command_on_modification(self, mock_subprocess_run):
        command = ["echo", "hello"]
        handler = CommandEventHandler(command, self.project_dir)

        # Simulate a file modification event
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.project_dir / "test.txt")

        handler.on_any_event(mock_event)

        mock_subprocess_run.assert_called_once_with(command, cwd=self.project_dir)

    @patch('subprocess.run')
    def test_command_event_handler_ignores_directories(self, mock_subprocess_run):
        command = ["echo", "hello"]
        handler = CommandEventHandler(command, self.project_dir)

        # Simulate a directory modification event
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(self.project_dir / "test_dir")

        handler.on_any_event(mock_event)

        mock_subprocess_run.assert_not_called()

    @patch('subprocess.run')
    def test_command_event_handler_ignores_specified_dirs(self, mock_subprocess_run):
        command = ["echo", "hello"]
        handler = CommandEventHandler(command, self.project_dir)

        ignored_paths = [
            self.project_dir / ".git" / "index",
            self.project_dir / "__pycache__" / "test.pyc",
            self.project_dir / "node_modules" / "lib" / "index.js",
        ]

        for path in ignored_paths:
            mock_event = MagicMock()
            mock_event.is_directory = False
            mock_event.src_path = str(path)

            handler.on_any_event(mock_event)

        mock_subprocess_run.assert_not_called()

    @patch('subprocess.run')
    @patch('shared.watch_handler.Observer')
    @patch('time.sleep', side_effect=KeyboardInterrupt)
    def test_start_watcher_runs_on_start(self, mock_sleep, mock_observer, mock_subprocess_run):
        command = ["echo", "started"]

        mock_observer_instance = mock_observer.return_value

        start_watcher(self.project_dir, command)

        # Check that the command was run on start
        mock_subprocess_run.assert_called_once_with(command, cwd=self.project_dir)

        # Check that the observer was set up
        mock_observer_instance.schedule.assert_called_once()
        mock_observer_instance.start.assert_called_once()
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()

if __name__ == '__main__':
    unittest.main()
