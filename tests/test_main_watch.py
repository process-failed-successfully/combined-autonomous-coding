import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import time
import os

from main import run_watch

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
        event_handler = CommandEventHandler(command_to_run, self.test_dir)
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.test_file)

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_subprocess_run.assert_called_once_with(command_to_run, cwd=self.test_dir)

    @patch('main.subprocess.run')
    def test_command_event_handler_ignores_directories(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['pytest']
        event_handler = CommandEventHandler(command_to_run, self.test_dir)
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(self.test_dir)

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
