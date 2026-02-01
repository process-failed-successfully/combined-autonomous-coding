import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.cli_kanban import run_kanban_logic
from shared.task_manager import Task

class TestCliKanban(unittest.TestCase):
    @patch("shared.cli_kanban.TaskManager")
    @patch("shared.cli_kanban.Console")
    def test_kanban_view(self, mock_console, mock_task_manager):
        # Setup mock tasks
        mock_tm_instance = mock_task_manager.return_value
        mock_tm_instance.fetch_all_tasks.return_value = [
            Task(id="GH-1", source="github", title="Fix bug", status="open"),
            Task(id="SPRINT-2", source="sprint", title="Feature X", status="in_progress"),
            Task(id="TODO-3", source="todo", title="Refactor", status="done")
        ]

        # Run
        project_dir = Path("/tmp/test")
        result = run_kanban_logic(project_dir, action="view")

        # Assert
        self.assertTrue(result)
        mock_tm_instance.fetch_all_tasks.assert_called_once()
        mock_console.return_value.print.assert_called()

    @patch("shared.cli_kanban.TaskManager")
    @patch("shared.cli_kanban.Console")
    def test_kanban_move_success(self, mock_console, mock_task_manager):
        mock_tm_instance = mock_task_manager.return_value
        mock_tm_instance.update_task_status.return_value = True

        result = run_kanban_logic(Path("."), action="move", task_id="SPRINT-1", status="done")

        self.assertTrue(result)
        mock_tm_instance.update_task_status.assert_called_once_with("SPRINT-1", "done")

    @patch("shared.cli_kanban.TaskManager")
    @patch("shared.cli_kanban.Console")
    def test_kanban_move_fail(self, mock_console, mock_task_manager):
        mock_tm_instance = mock_task_manager.return_value
        mock_tm_instance.update_task_status.return_value = False

        result = run_kanban_logic(Path("."), action="move", task_id="GH-1", status="done")

        self.assertFalse(result)
        mock_tm_instance.update_task_status.assert_called_once_with("GH-1", "done")

    @patch("shared.cli_kanban.Console")
    def test_kanban_move_missing_args(self, mock_console):
        result = run_kanban_logic(Path("."), action="move", task_id="GH-1") # Missing status
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
