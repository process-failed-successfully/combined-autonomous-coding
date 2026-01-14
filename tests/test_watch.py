
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_watch, CommandEventHandler

class TestWatchCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('main.sys.exit')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    @patch('main.Observer')
    def test_run_watch_setup_and_shutdown(self, mock_observer_class, mock_sleep, mock_exit):
        """Test that run_watch sets up the observer and shuts down gracefully."""
        mock_observer_instance = MagicMock()
        mock_observer_class.return_value = mock_observer_instance

        args = MagicMock()
        args.watch_command = ['ls']
        args.project_dir = self.test_dir

        run_watch(args)

        mock_observer_class.assert_called_once()
        mock_observer_instance.schedule.assert_called_once()
        mock_observer_instance.start.assert_called_once()

        # from the `except KeyboardInterrupt:` block
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()
        mock_exit.assert_called_once_with(0)

class TestCommandEventHandler(unittest.TestCase):

    @patch('main.subprocess.run')
    def test_on_modified_runs_command_for_file(self, mock_subprocess_run):
        """Test that the event handler runs the command on file modification."""
        command = ['echo', 'file changed']
        project_dir = '/tmp/project'
        handler = CommandEventHandler(command, project_dir)

        event = MagicMock()
        event.is_directory = False
        event.src_path = '/tmp/project/some_file.py'

        handler.on_modified(event)

        mock_subprocess_run.assert_called_once_with(command, cwd=project_dir)

    @patch('main.subprocess.run')
    def test_on_modified_ignores_directory(self, mock_subprocess_run):
        """Test that the event handler ignores directory modification events."""
        command = ['echo', 'file changed']
        project_dir = '/tmp/project'
        handler = CommandEventHandler(command, project_dir)

        event = MagicMock()
        event.is_directory = True
        event.src_path = '/tmp/project/a_directory/'

        handler.on_modified(event)

        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
