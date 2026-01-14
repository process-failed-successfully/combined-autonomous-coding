import argparse
import os
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from main import CommandEventHandler, run_watch


class TestWatchCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path("test_watch_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "test_file.txt"
        self.test_file.write_text("initial content")
        self.another_file = self.test_dir / "another.log"
        self.another_file.write_text("log content")

    def tearDown(self):
        self.test_file.unlink()
        self.another_file.unlink()
        self.test_dir.rmdir()

    @patch('main.Observer')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    def test_run_watch_starts_and_stops_observer(self, mock_sleep, mock_observer):
        # Arrange
        args = argparse.Namespace(
            project_dir=self.test_dir,
            watch_command=['ls'],
            patterns=['*'],
            ignore_patterns=[],
            clear=False,
            delay=0.1
        )
        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_watch(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_observer.assert_called_once()
        mock_observer_instance.schedule.assert_called_once()
        mock_observer_instance.start.assert_called_once()
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()

    @patch('main.subprocess.run')
    def test_handler_runs_command_on_modification(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['pytest', 'tests/']
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*.txt'], ignore_patterns=[], clear=False, delay=0
        )
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.test_file)

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_subprocess_run.assert_called_once_with(command_to_run, cwd=self.test_dir)

    @patch('main.subprocess.run')
    def test_handler_ignores_directories(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['pytest']
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*'], ignore_patterns=[], clear=False, delay=0
        )
        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = str(self.test_dir)

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_subprocess_run.assert_not_called()

    @patch('main.subprocess.run')
    def test_handler_respects_patterns(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['echo']
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*.txt'], ignore_patterns=[], clear=False, delay=0
        )
        txt_event = MagicMock(is_directory=False, src_path=str(self.test_file))
        log_event = MagicMock(is_directory=False, src_path=str(self.another_file))

        # Act
        event_handler.on_modified(txt_event)
        event_handler.on_modified(log_event)

        # Assert
        mock_subprocess_run.assert_called_once_with(command_to_run, cwd=self.test_dir)

    @patch('main.subprocess.run')
    def test_handler_respects_ignore_patterns(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['echo']
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*'], ignore_patterns=['*.log'], clear=False, delay=0
        )
        txt_event = MagicMock(is_directory=False, src_path=str(self.test_file))
        log_event = MagicMock(is_directory=False, src_path=str(self.another_file))

        # Act
        event_handler.on_modified(txt_event)
        event_handler.on_modified(log_event)

        # Assert
        mock_subprocess_run.assert_called_once_with(command_to_run, cwd=self.test_dir)

    @patch('os.system')
    @patch('main.subprocess.run')
    def test_handler_clears_screen_if_flagged(self, mock_subprocess_run, mock_os_system):
        # Arrange
        command_to_run = ['echo']
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*'], ignore_patterns=[], clear=True, delay=0
        )
        mock_event = MagicMock(is_directory=False, src_path=str(self.test_file))
        clear_command = 'cls' if os.name == 'nt' else 'clear'

        # Act
        event_handler.on_modified(mock_event)

        # Assert
        mock_os_system.assert_called_once_with(clear_command)
        mock_subprocess_run.assert_called_once()

    @patch('main.subprocess.run')
    def test_handler_debounces_events(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['echo']
        delay = 0.2
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*'], ignore_patterns=[], clear=False, delay=delay
        )
        mock_event = MagicMock(is_directory=False, src_path=str(self.test_file))

        # Act
        event_handler.on_modified(mock_event)  # First call
        time.sleep(delay / 4)
        event_handler.on_modified(mock_event)  # Second call, should be ignored
        time.sleep(delay / 4)
        event_handler.on_modified(mock_event)  # Third call, should be ignored

        # Assert
        mock_subprocess_run.assert_called_once()

    @patch('main.subprocess.run')
    def test_handler_runs_after_delay(self, mock_subprocess_run):
        # Arrange
        command_to_run = ['echo']
        delay = 0.1
        event_handler = CommandEventHandler(
            command_to_run, self.test_dir, patterns=['*'], ignore_patterns=[], clear=False, delay=delay
        )
        mock_event = MagicMock(is_directory=False, src_path=str(self.test_file))

        # Act
        event_handler.on_modified(mock_event)  # First call
        time.sleep(delay * 1.5)
        event_handler.on_modified(mock_event)  # Second call, should run

        # Assert
        self.assertEqual(mock_subprocess_run.call_count, 2)


if __name__ == '__main__':
    unittest.main()
