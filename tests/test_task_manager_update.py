import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import json
from shared.task_manager import TaskManager

class TestTaskManagerUpdate(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = TaskManager(self.project_dir)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.write_text")
    def test_update_sprint_task(self, mock_write, mock_read, mock_exists):
        mock_exists.return_value = True
        sprint_data = {
            "tasks": [
                {"id": "1", "title": "Task 1", "status": "PENDING"},
                {"id": "2", "title": "Task 2", "status": "PENDING"}
            ]
        }
        mock_read.return_value = json.dumps(sprint_data)

        # Test successful update
        success = self.manager.update_task_status("SPRINT-1", "IN_PROGRESS", "sprint")
        self.assertTrue(success)

        # Verify write
        args, _ = mock_write.call_args
        written_data = json.loads(args[0])
        self.assertEqual(written_data["tasks"][0]["status"], "IN_PROGRESS")

        # Test task not found
        success = self.manager.update_task_status("SPRINT-99", "DONE", "sprint")
        self.assertFalse(success)

    @patch("shared.task_manager.JiraClient")
    def test_update_jira_task(self, MockJiraClient):
        # Inject config directly
        self.manager.config = {
            "jira": {
                "url": "https://jira.example.com",
                "email": "user@example.com",
                "token": "token"
            }
        }

        mock_client_instance = MockJiraClient.return_value
        mock_client_instance.transition_issue.return_value = True

        success = self.manager.update_task_status("PROJ-123", "Done", "jira")
        self.assertTrue(success)
        mock_client_instance.transition_issue.assert_called_with("PROJ-123", "Done")

        # Test failure
        mock_client_instance.transition_issue.return_value = False
        success = self.manager.update_task_status("PROJ-123", "Unknown", "jira")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
