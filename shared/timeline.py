import json
import shutil
import subprocess
import io
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table

@dataclass
class TimelineEvent:
    timestamp: datetime
    type: str  # git, agent, release, session
    title: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata
        }

class TimelineCollector:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()

    def collect_git_events(self, limit: int = 50) -> List[TimelineEvent]:
        events = []
        git_path = shutil.which("git")
        if not git_path or not (self.project_dir / ".git").is_dir():
            return events

        try:
            # Format: ISO Date | Author | Message | Hash
            cmd = [git_path, "-C", str(self.project_dir), "log", f"-n{limit}", "--pretty=format:%aI|%an|%s|%h", "--date=iso"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return events

            for line in result.stdout.strip().split('\n'):
                if not line: continue
                parts = line.split('|', 3)
                if len(parts) == 4:
                    dt_str, author, msg, h = parts
                    try:
                        dt = datetime.fromisoformat(dt_str)
                        events.append(TimelineEvent(
                            timestamp=dt,
                            type="git",
                            title=f"Commit: {msg}",
                            description=f"Author: {author}, Hash: {h}",
                            metadata={"author": author, "hash": h}
                        ))
                    except ValueError:
                        pass
        except Exception:
            pass
        return events

    def collect_agent_events(self) -> List[TimelineEvent]:
        events = []
        # Assumes the script is running from the repo root or can find agents/logs
        # Adjust logic to find repo root based on this file location
        repo_root = Path(__file__).parent.parent
        logs_dir = repo_root / "agents/logs"

        if not logs_dir.exists():
            return events

        # Read history file to get valid runs for this project
        history_file = self.project_dir / ".agent_history"
        valid_runs = set()
        if history_file.exists():
            try:
                valid_runs = {line.strip() for line in history_file.read_text().splitlines() if line.strip()}
            except Exception:
                pass

        for log_file in logs_dir.glob("*.log"):
            run_id = log_file.stem

            # If we have a history file, only include runs in it.
            # Otherwise (fresh clone?), we might show all logs found in the global dir,
            # but that might be confusing. Let's strictly follow project history if available.
            if valid_runs and run_id not in valid_runs:
                continue

            try:
                stat = log_file.stat()
                dt = datetime.fromtimestamp(stat.st_ctime)

                # Try to extract more info from log content
                content = log_file.read_text(encoding="utf-8", errors="ignore")

                # Check for "Starting ... Agent"
                agent_type = "Unknown"
                if "Starting Gemini Agent" in content: agent_type = "Gemini"
                elif "Starting Cursor Agent" in content: agent_type = "Cursor"
                elif "Starting Local Agent" in content: agent_type = "Local"
                elif "Starting OpenRouter Agent" in content: agent_type = "OpenRouter"

                events.append(TimelineEvent(
                    timestamp=dt,
                    type="agent",
                    title=f"Agent Run: {run_id}",
                    description=f"Agent: {agent_type}",
                    metadata={"run_id": run_id, "agent_type": agent_type}
                ))
            except Exception:
                pass
        return events

    def collect_release_events(self) -> List[TimelineEvent]:
        events = []
        git_path = shutil.which("git")
        if not git_path or not (self.project_dir / ".git").is_dir():
            return events

        try:
            # Get tags with dates. --simplify-by-decoration ensures we only see commits with tags?
            # No, that simplifies history.
            # "git log --tags --date=iso --pretty=format:%aI|%D"
            # %D = ref names (HEAD -> main, tag: v1.0.0)
            cmd = [git_path, "-C", str(self.project_dir), "log", "--tags", "--no-walk", "--pretty=format:%aI|%D", "--date=iso"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            for line in result.stdout.strip().split('\n'):
                if not line: continue
                parts = line.split('|', 1)
                if len(parts) == 2:
                    dt_str, ref_names = parts
                    # ref_names looks like "tag: v0.1.0, tag: v0.1.1" or "HEAD -> main, tag: v1.0"
                    if "tag:" in ref_names:
                        try:
                            dt = datetime.fromisoformat(dt_str)
                            # Extract tag names
                            refs = [r.strip() for r in ref_names.split(",")]
                            tags = [t.replace("tag:", "").strip() for t in refs if "tag:" in t]

                            for tag in tags:
                                events.append(TimelineEvent(
                                    timestamp=dt,
                                    type="release",
                                    title=f"Release {tag}",
                                    description="Git Tag",
                                    metadata={"tag": tag}
                                ))
                        except ValueError:
                            pass
        except Exception:
            pass
        return events

    def collect_session_events(self) -> List[TimelineEvent]:
        events = []
        sessions_dir = self.project_dir / ".agent_sessions"
        if not sessions_dir.exists():
            return events

        for sess_file in sessions_dir.glob("*.json"):
            try:
                data = json.loads(sess_file.read_text())
                name = data.get("name")
                created = data.get("created_at")

                if created:
                    events.append(TimelineEvent(
                        timestamp=datetime.fromisoformat(created),
                        type="session",
                        title=f"Session Created: {name}",
                        description=data.get("description", ""),
                        metadata={"file": sess_file.name}
                    ))
            except Exception:
                pass
        return events

    def get_timeline(self, limit: int = 100) -> List[TimelineEvent]:
        events = []
        events.extend(self.collect_git_events(limit=limit))
        events.extend(self.collect_agent_events())
        events.extend(self.collect_release_events())
        events.extend(self.collect_session_events())

        # Sort desc (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        return events[:limit]

class TimelineRenderer:
    def get_rich_table(self, events: List[TimelineEvent]) -> Table:
        table = Table(title="Project Timeline", show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan", width=20)
        table.add_column("Type", width=10)
        table.add_column("Event", style="white")

        type_colors = {
            "git": "blue",
            "agent": "green",
            "release": "bold yellow",
            "session": "magenta"
        }

        if not events:
            # Return empty table or table with message
            return table

        for e in events:
            date_str = e.timestamp.strftime("%Y-%m-%d %H:%M")
            type_style = type_colors.get(e.type, "white")
            type_str = f"[{type_style}]{e.type.upper()}[/{type_style}]"

            desc = f"\n[dim]{e.description}[/dim]" if e.description else ""
            title = f"{e.title}{desc}"

            table.add_row(date_str, type_str, title)
        return table

    def render_text(self, events: List[TimelineEvent]) -> str:
        if not events:
            return "No timeline events found."

        console = Console(file=io.StringIO(), force_terminal=True)
        table = self.get_rich_table(events)
        console.print(table)
        return console.file.getvalue()

    def render_json(self, events: List[TimelineEvent]) -> str:
        return json.dumps([e.to_dict() for e in events], indent=2)

    def render_html(self, events: List[TimelineEvent]) -> str:
        # Vis.js data format
        items = []
        for i, e in enumerate(events):
            color = "#97C2FC" # Default blue (git)
            if e.type == "agent": color = "#7BE141" # Green
            elif e.type == "release": color = "#FFA500" # Orange
            elif e.type == "session": color = "#FB7E81" # Red

            items.append({
                "id": i,
                "content": e.title,
                "start": e.timestamp.isoformat(),
                "type": "point",
                "style": f"background-color: {color};",
                "title": e.description # Tooltip
            })

        json_items = json.dumps(items)

        return f"""<!DOCTYPE HTML>
<html>
<head>
  <title>Project Timeline</title>
  <script src="https://unpkg.com/vis-timeline/standalone/umd/vis-timeline-graph2d.min.js"></script>
  <link href="https://unpkg.com/vis-timeline/styles/vis-timeline-graph2d.min.css" rel="stylesheet" type="text/css" />
  <style type="text/css">
    body, html {{ font-family: sans-serif; }}
    #visualization {{ width: 100%; height: 600px; border: 1px solid lightgray; }}
  </style>
</head>
<body>
<h1>Project Timeline</h1>
<div id="visualization"></div>
<script type="text/javascript">
  var container = document.getElementById('visualization');
  var items = new vis.DataSet({json_items});
  var options = {{
    height: '600px',
    verticalScroll: true,
    zoomKey: 'ctrlKey',
    maxHeight: '600px',
    order: function(a, b) {{ return b.id - a.id; }} // Maintain stability
  }};
  var timeline = new vis.Timeline(container, items, options);
</script>
</body>
</html>
"""
