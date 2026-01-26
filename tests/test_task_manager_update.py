import unittest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.task_manager import TaskManager

class TestTaskManagerUpdate(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("test_project_tm_update")
        self.project_dir.mkdir(exist_ok=True)
        # We need to mock load_config_from_file so it doesn't try to read real config
        with patch("shared.task_manager.load_config_from_file", return_value={}):
            self.manager = TaskManager(self.project_dir)

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def test_update_sprint_task(self):
        # Create dummy sprint plan
        sprint_plan = {
            "tasks": [
                {"id": "1", "title": "Test Task", "status": "PENDING"}
            ]
        }
        plan_path = self.project_dir / "sprint_plan.json"
        plan_path.write_text(json.dumps(sprint_plan))

        # Update
        success = self.manager.update_task_status("SPRINT-1", "IN_PROGRESS")
        self.assertTrue(success)

        # Verify
        data = json.loads(plan_path.read_text())
        self.assertEqual(data["tasks"][0]["status"], "IN_PROGRESS")

    @patch("shared.task_manager.JiraClient")
    def test_update_jira_task(self, mock_jira_cls):
        # Manually set config
        self.manager.config = {"jira": {"url": "http://jira", "email": "e", "token": "t"}}

        mock_client = MagicMock()
        mock_jira_cls.return_value = mock_client
        mock_client.transition_issue.return_value = True

        success = self.manager.update_task_status("PROJ-123", "IN_PROGRESS")
        self.assertTrue(success)
        mock_client.transition_issue.assert_called_with("PROJ-123", "In Progress")

    def test_update_unknown_source(self):
        success = self.manager.update_task_status("TODO-1", "Done")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()
