import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.cli_kanban import run_kanban_logic
from shared.task_manager import Task

class TestCliKanban(unittest.TestCase):
    @patch('shared.cli_kanban.TaskManager')
    @patch('shared.cli_kanban.Console')
    def test_run_kanban_view(self, MockConsole, MockTaskManager):
        # Setup
        mock_manager = MockTaskManager.return_value
        mock_console = MockConsole.return_value

        # Mock tasks
        mock_manager.fetch_all_tasks.return_value = [
            Task(id="1", source="github", title="Task 1", status="open", priority="High"),
            Task(id="2", source="jira", title="Task 2", status="in_progress", priority="Medium"),
            Task(id="3", source="sprint", title="Task 3", status="done", priority="Low")
        ]

        # Execute
        result = run_kanban_logic(Path("."), "view")

        # Assert
        self.assertTrue(result)
        mock_manager.fetch_all_tasks.assert_called_once()
        mock_console.print.assert_called_once()

    @patch('shared.cli_kanban.TaskManager')
    @patch('shared.cli_kanban.Console')
    def test_run_kanban_move_success(self, MockConsole, MockTaskManager):
        # Setup
        mock_manager = MockTaskManager.return_value
        mock_console = MockConsole.return_value
        mock_manager.update_task_status.return_value = True

        # Execute
        result = run_kanban_logic(Path("."), "move", task_id="123", status="done")

        # Assert
        self.assertTrue(result)
        mock_manager.update_task_status.assert_called_once_with("123", "done")

        # Verify success message
        # We need to check call args. Since console.print is called multiple times (moving..., success msg)
        # we check if any call contains success message
        found = False
        for call in mock_console.print.call_args_list:
            if "updated successfully" in str(call):
                found = True
                break
        self.assertTrue(found)

    @patch('shared.cli_kanban.TaskManager')
    @patch('shared.cli_kanban.Console')
    def test_run_kanban_move_failure(self, MockConsole, MockTaskManager):
        # Setup
        mock_manager = MockTaskManager.return_value
        mock_console = MockConsole.return_value
        mock_manager.update_task_status.return_value = False

        # Execute
        result = run_kanban_logic(Path("."), "move", task_id="123", status="done")

        # Assert
        self.assertFalse(result)
        mock_manager.update_task_status.assert_called_once_with("123", "done")

        # Verify failure message
        found = False
        for call in mock_console.print.call_args_list:
            if "Failed to update task" in str(call):
                found = True
                break
        self.assertTrue(found)

    @patch('shared.cli_kanban.Console')
    def test_run_kanban_move_missing_args(self, MockConsole):
        # Execute
        result = run_kanban_logic(Path("."), "move") # Missing task_id and status

        # Assert
        self.assertFalse(result)
