
import unittest
from unittest.mock import patch, MagicMock, call
import time
import os
import sys
from pathlib import Path
import argparse

# Make sure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import CommandEventHandler, run_watch

class TestWatchFunctionality(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path('./test_watch_project')
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch('main.subprocess.run')
    @patch('main.os.system')
    def test_command_execution_with_clear(self, mock_os_system, mock_subprocess_run):
        handler = CommandEventHandler(
            command=['pytest'],
            project_dir=self.project_dir,
            clear_screen=True
        )
        handler._run_command()
        mock_os_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')
        mock_subprocess_run.assert_called_once_with(['pytest'], cwd=self.project_dir)

    @patch('main.Timer')
    def test_debouncing_logic(self, mock_timer_class):
        mock_timer_instance = MagicMock()
        mock_timer_class.return_value = mock_timer_instance

        handler = CommandEventHandler(
            command=['echo', 'change'],
            project_dir=self.project_dir,
            delay=0.5
        )

        mock_event = MagicMock()
        mock_event.src_path = str(self.project_dir / 'test.txt')

        handler.on_modified(mock_event)
        handler.on_modified(mock_event)

        self.assertEqual(mock_timer_instance.cancel.call_count, 1)
        self.assertEqual(mock_timer_class.call_count, 2)
        mock_timer_instance.start.assert_called()


class TestWatchCommandIntegration(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path('./test_watch_project_integration')
        self.project_dir.mkdir(exist_ok=True)
        (self.project_dir / 'test.py').touch()
        (self.project_dir / 'test.txt').touch()
        self.pycache_dir = self.project_dir / '__pycache__'
        self.pycache_dir.mkdir(exist_ok=True)
        (self.pycache_dir / 'cache_file.pyc').touch()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.project_dir)

    @patch('main.Observer')
    @patch('main.time.sleep', side_effect=KeyboardInterrupt)
    def test_watch_with_patterns_and_ignores(self, mock_sleep, mock_observer_class):
        mock_observer_instance = MagicMock()
        mock_observer_class.return_value = mock_observer_instance

        args = argparse.Namespace(
            project_dir=self.project_dir,
            watch_command=['pytest'],
            patterns=['*.py'],
            ignore_patterns=['*/__pycache__/*'],
            delay=0.1,
            clear=False
        )

        with self.assertRaises(SystemExit) as cm:
            run_watch(args)

        self.assertEqual(cm.exception.code, 0)

        # Check that the event handler was scheduled with the correct patterns
        call_args, call_kwargs = mock_observer_instance.schedule.call_args
        handler = call_args[0]

        self.assertEqual(handler.patterns, ['*.py'])
        self.assertEqual(handler.ignore_patterns, ['*/__pycache__/*'])

if __name__ == '__main__':
    unittest.main()
