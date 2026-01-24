import json
import os
import uuid
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
        tasks.extend(self.fetch_features())
        tasks.extend(self.fetch_github_issues())
        tasks.extend(self.fetch_jira_tickets())
        tasks.extend(self.fetch_sprint_tasks())
        tasks.extend(self.fetch_todos())
        return tasks

    def fetch_features(self) -> List[Task]:
        """Fetches features from feature_list.json."""
        feature_file = self.project_dir / "feature_list.json"
        if not feature_file.exists():
            return []

        try:
            content = feature_file.read_text()
            if not content.strip():
                return []

            data = json.loads(content)
            tasks = []
            for feat in data.get("features", []):
                status = "Done" if feat.get("passes") else "Pending"
                tasks.append(Task(
                    id=feat.get("id", str(uuid.uuid4())[:8]),
                    source="feature",
                    title=feat.get("title", "Untitled Feature"),
                    status=status,
                    priority="High",  # Features are high level goals
                    metadata={"description": feat.get("description", "")}
                ))
            return tasks
        except Exception:
            return []

    def add_feature(self, title: str, description: str) -> bool:
        """Adds a new feature to feature_list.json."""
        feature_file = self.project_dir / "feature_list.json"

        try:
            if feature_file.exists() and feature_file.stat().st_size > 0:
                data = json.loads(feature_file.read_text())
            else:
                data = {"features": []}

            if "features" not in data:
                data["features"] = []

            # Generate simple ID if title is simple, else UUID
            import re
            slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
            if not slug:
                slug = str(uuid.uuid4())[:8]

            # Ensure unique ID
            existing_ids = {f.get("id") for f in data["features"]}
            if slug in existing_ids:
                slug = f"{slug}_{str(uuid.uuid4())[:4]}"

            new_feature = {
                "id": slug,
                "title": title,
                "description": description,
                "passes": False
            }

            data["features"].append(new_feature)
            feature_file.write_text(json.dumps(data, indent=2))
            return True
        except Exception as e:
            print(f"Error adding feature: {e}")
            return False

    def update_feature_status(self, feature_id: str, status: str) -> bool:
        """Updates the status of a feature (passes: true/false)."""
        feature_file = self.project_dir / "feature_list.json"
        if not feature_file.exists():
            return False

        try:
            data = json.loads(feature_file.read_text())
            features = data.get("features", [])

            found = False
            for feat in features:
                if feat.get("id") == feature_id:
                    # Map status to passes boolean
                    if status.lower() in ["done", "passed", "true", "completed"]:
                        feat["passes"] = True
                    else:
                        feat["passes"] = False
                    found = True
                    break

            if found:
                feature_file.write_text(json.dumps(data, indent=2))
                return True
            return False
        except Exception:
            return False

    def delete_feature(self, feature_id: str) -> bool:
        """Deletes a feature from feature_list.json."""
        feature_file = self.project_dir / "feature_list.json"
        if not feature_file.exists():
            return False

        try:
            data = json.loads(feature_file.read_text())
            features = data.get("features", [])

            new_features = [f for f in features if f.get("id") != feature_id]

            if len(new_features) < len(features):
                data["features"] = new_features
                feature_file.write_text(json.dumps(data, indent=2))
                return True
            return False
        except Exception:
            return False

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
