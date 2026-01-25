import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from shared.config_loader import load_config_from_file
from shared.github_client import GitHubClient
from shared.jira_client import JiraClient
from shared.todos import scan_todos
from shared.config import JiraConfig

@dataclass
class Task:
    id: str
    source: str  # "github", "jira", "sprint", "todo"
    title: str
    status: str
    priority: str = "Medium"
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskManager:
    """
    Aggregates tasks from various sources:
    - GitHub Issues
    - Jira Tickets
    - Sprint Plan
    - Local TODOs
    """

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.config = load_config_from_file()

    def fetch_all_tasks(self) -> List[Task]:
        """Fetches all tasks from all configured sources."""
        tasks = []
        tasks.extend(self.fetch_github_issues())
        tasks.extend(self.fetch_jira_tickets())
        tasks.extend(self.fetch_sprint_tasks())
        tasks.extend(self.fetch_todos())
        return tasks

    def fetch_github_issues(self) -> List[Task]:
        """Fetches open issues from GitHub."""
        token = self.config.get("github_token") or os.environ.get("GITHUB_TOKEN")
        host = self.config.get("github_host", "github.com")

        if not token:
            return []

        try:
            client = GitHubClient(token=token, host=host)
            issues = client.get_issues(self.project_dir, state="open")
            tasks = []
            for issue in issues:
                # Determine priority from labels
                priority = "Medium"
                labels = [l['name'].lower() for l in issue.get('labels', [])]
                if "high" in labels or "urgent" in labels:
                    priority = "High"
                elif "low" in labels:
                    priority = "Low"

                tasks.append(Task(
                    id=f"GH-{issue['number']}",
                    source="github",
                    title=issue['title'],
                    status=issue['state'],
                    priority=priority,
                    url=issue['html_url'],
                    metadata={"assignee": issue['assignee']['login'] if issue['assignee'] else None}
                ))
            return tasks
        except Exception:
            # Log error? For now just return empty list to avoid crashing TUI
            return []

    def fetch_jira_tickets(self) -> List[Task]:
        """Fetches tickets from Jira if configured."""
        jira_cfg = self.config.get("jira", {})
        url = jira_cfg.get("url") or os.environ.get("JIRA_URL")
        email = jira_cfg.get("email") or os.environ.get("JIRA_EMAIL")
        token = jira_cfg.get("token") or os.environ.get("JIRA_TOKEN")

        if not (url and email and token):
            return []

        try:
            config = JiraConfig(url=url, email=email, token=token)
            client = JiraClient(config)
            # Fetch assigned to me or open? Let's fetch open issues for the project?
            # Or just "To Do"? Let's try a generic JQL.
            # Assuming we want to see what's relevant.
            # Maybe just assigned to current user? Or everything?
            # Let's try fetching "To Do" and "In Progress"
            jql = 'statusCategory in ("To Do", "In Progress") ORDER BY updated DESC'
            issues = client.search_issues(jql, max_results=20)

            tasks = []
            for issue in issues:
                tasks.append(Task(
                    id=issue.key,
                    source="jira",
                    title=issue.fields.summary,
                    status=str(issue.fields.status),
                    priority=str(issue.fields.priority) if hasattr(issue.fields, "priority") else "Medium",
                    url=f"{url}/browse/{issue.key}",
                    metadata={"assignee": str(issue.fields.assignee) if issue.fields.assignee else None}
                ))
            return tasks
        except Exception:
            return []

    def fetch_sprint_tasks(self) -> List[Task]:
        """Fetches tasks from sprint_plan.json."""
        sprint_plan_path = self.project_dir / "sprint_plan.json"
        if not sprint_plan_path.exists():
            return []

        try:
            data = json.loads(sprint_plan_path.read_text())
            tasks = []
            for t in data.get("tasks", []):
                status = t.get("status", "PENDING")
                # Filter out completed if we want only active tasks?
                # Let's keep all but maybe sort/filter in UI.

                tasks.append(Task(
                    id=f"SPRINT-{t.get('id')}",
                    source="sprint",
                    title=t.get("title", "No Title"),
                    status=status,
                    priority="High" if status == "IN_PROGRESS" else "Medium",
                    metadata={"description": t.get("description")}
                ))
            return tasks
        except Exception:
            return []

    def fetch_todos(self) -> List[Task]:
        """Fetches TODOs from the codebase."""
        try:
            todos = scan_todos(self.project_dir)
            tasks = []
            for i, todo in enumerate(todos):
                # Limit to 50 TODOs to avoid clutter?
                if i >= 50:
                    break

                title = f"{todo['tag']}: {todo['text']}"
                if len(title) > 60:
                    title = title[:57] + "..."

                tasks.append(Task(
                    id=f"TODO-{i+1}",
                    source="todo",
                    title=title,
                    status="Open",
                    priority="Low",
                    metadata={
                        "file": todo['file'],
                        "line": todo['line']
                    }
                ))
            return tasks
        except Exception:
            return []

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """
        Updates the status of a task.
        Returns True if successful, False otherwise.
        """
        if task_id.startswith("SPRINT-"):
            return self._update_sprint_task(task_id, new_status)
        elif not task_id.startswith("GH-") and not task_id.startswith("TODO-"):
            # Assume Jira if no prefix or standard Jira key format (PROJECT-123)
            return self._update_jira_task(task_id, new_status)

        return False

    def _update_sprint_task(self, task_id: str, new_status: str) -> bool:
        sprint_plan_path = self.project_dir / "sprint_plan.json"
        if not sprint_plan_path.exists():
            return False

        try:
            data = json.loads(sprint_plan_path.read_text())
            raw_id = task_id.replace("SPRINT-", "")

            updated = False
            for task in data.get("tasks", []):
                if str(task.get("id")) == raw_id:
                    task["status"] = new_status
                    updated = True
                    break

            if updated:
                sprint_plan_path.write_text(json.dumps(data, indent=2))
                return True
            return False
        except Exception:
            return False

    def _update_jira_task(self, task_id: str, new_status: str) -> bool:
        jira_cfg = self.config.get("jira", {})
        url = jira_cfg.get("url") or os.environ.get("JIRA_URL")
        email = jira_cfg.get("email") or os.environ.get("JIRA_EMAIL")
        token = jira_cfg.get("token") or os.environ.get("JIRA_TOKEN")

        if not (url and email and token):
            return False

        try:
            config = JiraConfig(url=url, email=email, token=token)
            client = JiraClient(config)
            # Jira transition requires finding the transition ID or name.
            # JiraClient.transition_issue handles name matching.
            return client.transition_issue(task_id, new_status)
        except Exception:
            return False
