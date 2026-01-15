import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_watch, CommandEventHandler

class TestWatchCommand(unittest.TestCase):

    @patch('main.Observer')
    @patch('main.subprocess.run')
    def test_run_watch_starts_observer_and_runs_initial_command(self, mock_subprocess_run, mock_observer_class):
        """
        Tests that the `run_watch` function correctly starts the watchdog observer
        and runs the provided command upon initialization.
        """
        # --- Setup ---
        mock_observer_instance = MagicMock()
        mock_observer_class.return_value = mock_observer_instance
        project_dir = Path("./dummy_project")
        command_to_run = ["echo", "hello"]
        args = MagicMock(project_dir=project_dir, watch_command=command_to_run)

        # --- Action & Assertions for SystemExit ---
        with self.assertRaises(SystemExit) as cm:
            # Mock time.sleep to raise KeyboardInterrupt to stop the infinite loop
            with patch('time.sleep', side_effect=KeyboardInterrupt):
                run_watch(args)

        self.assertEqual(cm.exception.code, 0)

        # --- Other Assertions ---
        mock_subprocess_run.assert_called_once_with(command_to_run, cwd=project_dir.resolve())
        mock_observer_class.assert_called_once()
        mock_observer_instance.schedule.assert_called_once()
        mock_observer_instance.start.assert_called_once()
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()

    @patch('main.subprocess.run')
    def test_command_event_handler_triggers_command_on_modification(self, mock_subprocess_run):
        """
        Tests that the CommandEventHandler correctly calls subprocess.run
        when a file modification event occurs in a valid path.
        """
        # --- Setup ---
        project_dir = Path("./another_dummy_project").resolve()
        command = ["pytest"]
        event_handler = CommandEventHandler(command, project_dir)

        # Create a mock event for a file modification
        mock_event = MagicMock()
        mock_event.is_directory = False
        # Use a resolved path to mimic real-world behavior
        mock_event.src_path = str(project_dir / "app/main.py")

        # --- Action ---
        event_handler.on_any_event(mock_event)

        # --- Assertions ---
        # Check that the command was run with the correct, resolved path
        mock_subprocess_run.assert_called_once_with(command, cwd=project_dir)

    @patch('main.subprocess.run')
    def test_command_event_handler_ignores_git_directory(self, mock_subprocess_run):
        """
        Tests that the CommandEventHandler ignores events that occur inside
        the .git directory to prevent feedback loops from git operations.
        """
        # --- Setup ---
        project_dir = Path("./git_project").resolve()
        # Create the .git directory to make the path exist for the test
        (project_dir / ".git").mkdir(parents=True, exist_ok=True)

        command = ["make", "build"]
        event_handler = CommandEventHandler(command, project_dir)

        # Create a mock event for a file change inside .git/
        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = str(project_dir / ".git" / "index")

        # --- Action ---
        event_handler.on_any_event(mock_event)

        # --- Assertions ---
        # Verify that subprocess.run was NOT called
        mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
