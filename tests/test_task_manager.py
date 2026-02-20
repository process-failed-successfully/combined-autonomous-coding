import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import tempfile
import shutil
import json

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.task_manager import TaskManager  # noqa: E402


class TestTaskManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()
        # We delay instantiation if we want to mock config loaded in __init__
        # But here we can just mock self.manager.config directly after init
        with patch("shared.task_manager.load_config_from_file") as mock_load:
            mock_load.return_value = {}
            self.manager = TaskManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.task_manager.scan_todos")
    def test_fetch_todos(self, mock_scan):
        mock_scan.return_value = [
            {"file": "main.py", "line": 10, "tag": "TODO", "text": "Fix bug"}
        ]

        tasks = self.manager.fetch_todos()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].source, "todo")
        self.assertEqual(tasks[0].title, "TODO: Fix bug")
        self.assertEqual(tasks[0].metadata["file"], "main.py")

    def test_fetch_sprint_tasks(self):
        sprint_plan = {
            "sprint_goal": "Goal",
            "tasks": [
                {"id": "1", "title": "Task 1", "status": "PENDING", "description": "Desc 1"},
                {"id": "2", "title": "Task 2", "status": "IN_PROGRESS", "description": "Desc 2"}
            ]
        }
        (self.project_dir / "sprint_plan.json").write_text(json.dumps(sprint_plan))

        tasks = self.manager.fetch_sprint_tasks()
        self.assertEqual(len(tasks), 2)

        t1 = next(t for t in tasks if t.id == "SPRINT-1")
        self.assertEqual(t1.source, "sprint")
        self.assertEqual(t1.status, "PENDING")
        self.assertEqual(t1.priority, "Medium")

        t2 = next(t for t in tasks if t.id == "SPRINT-2")
        self.assertEqual(t2.status, "IN_PROGRESS")
        self.assertEqual(t2.priority, "High")

    @patch("shared.task_manager.GitHubClient")
    def test_fetch_github_issues(self, mock_gh_class):
        # Setup config
        self.manager.config = {"github_token": "fake"}

        mock_gh = mock_gh_class.return_value
        mock_gh.get_issues.return_value = [
            {"number": 101, "title": "GH Issue", "state": "open", "labels": [], "html_url": "url", "assignee": None}
        ]

        tasks = self.manager.fetch_github_issues()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "GH-101")
        self.assertEqual(tasks[0].source, "github")

    @patch("shared.task_manager.JiraClient")
    def test_fetch_jira_tickets(self, mock_jira_class):
        # Setup config
        self.manager.config = {
            "jira": {"url": "u", "email": "e", "token": "t"}
        }

        mock_jira = mock_jira_class.return_value

        mock_issue = MagicMock()
        mock_issue.key = "PROJ-1"
        mock_issue.fields.summary = "Jira Ticket"
        mock_issue.fields.status = "To Do"
        mock_issue.fields.assignee = None
        # Mock hasattr for priority by setting attribute
        mock_issue.fields.priority = "High"
        # Set date fields to None or valid strings to avoid TypeError/ValueError in logic
        mock_issue.fields.created = "2023-10-01T12:00:00Z"
        mock_issue.fields.duedate = "2023-10-15"

        mock_jira.search_issues.return_value = [mock_issue]

        tasks = self.manager.fetch_jira_tickets()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "PROJ-1")
        self.assertEqual(tasks[0].source, "jira")


if __name__ == "__main__":
    unittest.main()
