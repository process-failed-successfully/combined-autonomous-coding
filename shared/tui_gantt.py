from pathlib import Path
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set

from textual.app import ComposeResult
from textual.widgets import Label, Button, Static
from textual.containers import VerticalScroll, Horizontal, Vertical, Container
from textual.reactive import reactive
from textual import on

from shared.task_manager import Task

# Constants for visualization
UNIT_WIDTH = 4  # Characters per time unit

class GanttBar(Static):
    """Visual representation of a task duration."""

    def __init__(self, task: Task, start_time: int, duration: int = 1, **kwargs) -> None:
        super().__init__(" " * (duration * UNIT_WIDTH), **kwargs)
        self.gantt_task = task
        self.start_time = start_time
        self.duration = duration

        # Set styles dynamically based on task status
        self.add_class("gantt-bar")

        status = str(task.status).lower().replace("-", "_")
        if status in ["completed", "done", "fixed", "resolved"]:
            self.add_class("gantt-bar-completed")
        elif status in ["in_progress", "active", "developing"]:
            self.add_class("gantt-bar-active")
        elif status in ["failed", "blocked"]:
            self.add_class("gantt-bar-blocked")
        else:
            self.add_class("gantt-bar-pending")

    def on_mount(self) -> None:
        # Calculate left margin based on start time
        margin_left = self.start_time * UNIT_WIDTH
        self.styles.margin = (0, 0, 0, margin_left)
        self.styles.width = self.duration * UNIT_WIDTH

class GanttRow(Horizontal):
    """A row in the Gantt chart containing label and bar."""

    def __init__(self, task: Task, start_time: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.gantt_task = task
        self.start_time = start_time
        self.add_class("gantt-row")

    def compose(self) -> ComposeResult:
        # Task ID/Title Label
        title = f"{self.gantt_task.id}: {self.gantt_task.title}"
        if len(title) > 25:
            title = title[:22] + "..."
        yield Label(f"{title:<25}", classes="gantt-label")

        # The Bar
        yield GanttBar(self.gantt_task, self.start_time)

class GanttChart(VerticalScroll):
    """Container for the Gantt chart rows."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.tasks: List[Task] = []
        self.schedule: Dict[str, int] = {} # Task ID -> Start Time

    def compose(self) -> ComposeResult:
        yield Label("Load a Sprint Plan to view the schedule.", id="gantt-status")

    def load_schedule(self) -> None:
        # 1. Load tasks from sprint_plan.json
        sprint_plan_path = self.project_dir / "sprint_plan.json"
        if not sprint_plan_path.exists():
            self.query_one("#gantt-status", Label).update("No sprint_plan.json found.")
            return

        try:
            data = json.loads(sprint_plan_path.read_text())
            raw_tasks = data.get("tasks", [])
            self.tasks = []
            for t in raw_tasks:
                self.tasks.append(Task(
                    id=t.get("id"),
                    source="sprint",
                    title=t.get("title", "No Title"),
                    status=t.get("status", "PENDING"),
                    priority="Medium",
                    metadata={"dependencies": t.get("dependencies", [])}
                ))
        except Exception as e:
            self.query_one("#gantt-status", Label).update(f"Error loading plan: {e}")
            return

        if not self.tasks:
            self.query_one("#gantt-status", Label).update("Sprint Plan is empty.")
            return

        # 2. Calculate Schedule (EST)
        self.calculate_schedule()

        # 3. Render
        self.render_chart()

    def calculate_schedule(self) -> None:
        """Calculates Earliest Start Time (EST) for each task."""
        self.schedule = {}

        # Build dependency map
        adj = {t.id: t.metadata.get("dependencies", []) for t in self.tasks}

        # Simple iterative approach (bellman-ford-ish but for DAG max path)
        # Since we assume DAG, we can also do topological sort, but relaxation is easier to implement quickly.
        # Max rounds = len(tasks) to propagate dependencies

        # Init all to 0
        for t in self.tasks:
            self.schedule[t.id] = 0

        # Relax edges
        # Start Time = Max(Start Time of Dependency + Duration of Dependency)
        # Assuming Duration = 1 for all
        duration = 1

        changes = True
        rounds = 0
        max_rounds = len(self.tasks) + 1

        while changes and rounds < max_rounds:
            changes = False
            rounds += 1
            for t in self.tasks:
                current_start = self.schedule[t.id]
                dependencies = t.metadata.get("dependencies", [])

                max_dep_end = 0
                for dep_id in dependencies:
                    # Find dependency task (optimize by map if needed)
                    # We rely on schedule map which has all IDs initialized
                    if dep_id in self.schedule:
                        dep_end = self.schedule[dep_id] + duration
                        if dep_end > max_dep_end:
                            max_dep_end = dep_end

                if max_dep_end > current_start:
                    self.schedule[t.id] = max_dep_end
                    changes = True

        if rounds >= max_rounds:
            # Cycle detected or logic error, fallback is handled (tasks start late)
            pass

    def render_chart(self) -> None:
        # Clear existing rows
        for child in self.query(GanttRow):
            child.remove()

        self.query_one("#gantt-status", Label).update(f"Sprint Schedule ({len(self.tasks)} tasks)")

        # Sort tasks by start time then ID
        sorted_tasks = sorted(self.tasks, key=lambda t: (self.schedule.get(t.id, 0), t.id))

        for task in sorted_tasks:
            start = self.schedule.get(task.id, 0)
            self.mount(GanttRow(task, start))

class GanttTab(Container):
    """Tab for Gantt Chart visualization."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.chart = GanttChart(project_dir)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("[bold]Sprint Gantt Chart[/bold]", classes="welcome-text")

            with Horizontal(classes="stat-box"):
                yield Button("Refresh", id="btn-gantt-refresh", variant="primary")
                yield Label("1 Unit = 4 chars", classes="label")

            # Header Row
            with Horizontal(classes="gantt-header"):
                yield Label(f"{'Task':<25}", classes="gantt-label-header")
                yield Label("Timeline ->")

            yield self.chart

    def on_mount(self) -> None:
        self.chart.load_schedule()

    @on(Button.Pressed, "#btn-gantt-refresh")
    def on_refresh(self) -> None:
        self.chart.load_schedule()
