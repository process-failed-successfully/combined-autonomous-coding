
import unittest
from unittest.mock import patch, MagicMock, call
import argparse
from pathlib import Path
import sys
import os

# To ensure 'main' can be imported from the test directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main

class TestWatchCommand(unittest.TestCase):
    @patch('main.Observer')
    @patch('main.CommandEventHandler')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    def test_run_watch_starts_and_stops_observer(self, mock_sleep, mock_handler, mock_observer_cls):
        """
        Tests that the watch command initializes and starts the Observer,
        and then gracefully stops it on KeyboardInterrupt.
        """
        mock_observer_instance = MagicMock()
        mock_observer_cls.return_value = mock_observer_instance

        mock_handler_instance = MagicMock()
        mock_handler.return_value = mock_handler_instance

        args = main.parse_args(['watch', 'echo', 'hello'])

        with self.assertRaises(SystemExit) as cm:
            main.run_watch(args)

        self.assertEqual(cm.exception.code, 0)

        mock_handler.assert_called_once_with(['echo', 'hello'], Path('.').resolve())
        mock_observer_instance.schedule.assert_called_once_with(mock_handler_instance, Path('.').resolve(), recursive=True)
        mock_observer_instance.start.assert_called_once()
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()

    @patch('main.subprocess.run')
    def test_command_event_handler_on_modified(self, mock_subprocess_run):
        """
        Tests that the CommandEventHandler executes the specified command
        when a file modification event occurs.
        """
        project_dir = Path('/fake/project')
        command = ['pytest', '-k', 'test_something']

        handler = main.CommandEventHandler(command, project_dir)

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = '/fake/project/test_file.py'

        handler.on_modified(mock_event)

        mock_subprocess_run.assert_called_once_with(command, cwd=project_dir)

    @patch('main.subprocess.run')
    def test_command_event_handler_ignores_directories(self, mock_subprocess_run):
        """
        Tests that the CommandEventHandler ignores modification events
        that are for directories.
        """
        project_dir = Path('/fake/project')
        command = ['ls', '-l']

        handler = main.CommandEventHandler(command, project_dir)

        mock_event = MagicMock()
        mock_event.is_directory = True
        mock_event.src_path = '/fake/project/a_directory/'

        handler.on_modified(mock_event)

        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
