import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import json
from shared.task_manager import TaskManager, Task

class TestTaskManagerUpdate(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = TaskManager(self.project_dir)

    @patch("builtins.open", new_callable=mock_open, read_data='{"tasks": [{"id": 1, "title": "Task 1", "status": "PENDING"}]}')
    @patch("json.dump")
    @patch("pathlib.Path.exists")
    def test_update_sprint_task(self, mock_exists, mock_json_dump, mock_file):
        mock_exists.return_value = True
        # Test updating a sprint task
        success = self.manager.update_task_status("SPRINT-1", "sprint", "In Progress")

        self.assertTrue(success)

        # Verify json.dump was called with updated status
        args, _ = mock_json_dump.call_args
        data = args[0]
        self.assertEqual(data["tasks"][0]["status"], "IN_PROGRESS")

    @patch("shared.task_manager.JiraClient")
    def test_update_jira_task(self, MockJiraClient):
        # Mock config to enable Jira
        self.manager.config = {
            "jira": {
                "url": "https://jira.example.com",
                "email": "user@example.com",
                "token": "token"
            }
        }

        mock_client_instance = MockJiraClient.return_value
        mock_client_instance.transition_issue.return_value = True

        success = self.manager.update_task_status("PROJ-123", "jira", "Done")

        self.assertTrue(success)
        mock_client_instance.transition_issue.assert_called_with("PROJ-123", "Done")

    def test_update_unsupported_source(self):
        success = self.manager.update_task_status("GH-1", "github", "Done")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
