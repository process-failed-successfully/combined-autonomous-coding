import unittest
import json
import shutil
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.task_manager import TaskManager

class TestTaskManagerUpdate(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_tasks_tm")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.tm = TaskManager(self.test_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_update_sprint_task(self):
        # Create sprint plan
        plan = {
            "tasks": [
                {"id": "101", "title": "Test Task", "status": "PENDING"}
            ]
        }
        (self.test_dir / "sprint_plan.json").write_text(json.dumps(plan))

        result = self.tm.update_task_status("SPRINT-101", "sprint", "in_progress")
        self.assertTrue(result)

        # Verify update
        new_data = json.loads((self.test_dir / "sprint_plan.json").read_text())
        self.assertEqual(new_data["tasks"][0]["status"], "IN_PROGRESS")

    @patch("shared.task_manager.JiraClient")
    def test_update_jira_task(self, MockJiraClient):
        # Mock Config
        with patch.dict(os.environ, {"JIRA_URL": "http://jira", "JIRA_EMAIL": "u", "JIRA_TOKEN": "t"}):
            # Since TaskManager loads config in init, we might need to reload or mock load_config
            # But the update_jira_task reads config/env inside the method.

            mock_client = MockJiraClient.return_value
            mock_client.transition_issue.return_value = True

            result = self.tm.update_task_status("PROJ-123", "jira", "done")
            self.assertTrue(result)

            mock_client.transition_issue.assert_called_with("PROJ-123", "Done")

if __name__ == "__main__":
    unittest.main()
