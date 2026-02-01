import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, field
import shutil

from shared.task_manager import Task

class GanttCLI:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.tasks: List[Task] = []
        self.schedule: Dict[str, int] = {} # Task ID -> Start Time (0-indexed units)

    def load_tasks(self) -> bool:
        sprint_plan_path = self.project_dir / "sprint_plan.json"
        if not sprint_plan_path.exists():
            print(f"❌ Error: sprint_plan.json not found in {self.project_dir}")
            return False

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
            return True
        except Exception as e:
            print(f"❌ Error loading sprint plan: {e}")
            return False

    def calculate_schedule(self) -> None:
        """Calculates Earliest Start Time (EST) for each task."""
        self.schedule = {}
        # Init all to 0
        for t in self.tasks:
            self.schedule[t.id] = 0

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
                    if dep_id in self.schedule:
                        dep_end = self.schedule[dep_id] + duration
                        if dep_end > max_dep_end:
                            max_dep_end = dep_end

                if max_dep_end > current_start:
                    self.schedule[t.id] = max_dep_end
                    changes = True

    def render(self) -> None:
        if not self.tasks:
            print("Sprint Plan is empty.")
            return

        # Sort tasks by start time then ID
        sorted_tasks = sorted(self.tasks, key=lambda t: (self.schedule.get(t.id, 0), t.id))

        # Determine max time to scale chart if needed
        max_time = 0
        for t in self.tasks:
            end_time = self.schedule.get(t.id, 0) + 1
            if end_time > max_time:
                max_time = end_time

        print(f"--- Sprint Gantt Chart ({len(self.tasks)} tasks) ---")
        print(f"{'Task':<25} | Timeline")
        print("-" * (25 + 3 + max_time * 4)) # Approx width

        for t in sorted_tasks:
            start = self.schedule.get(t.id, 0)

            # Formatting
            title = f"{t.id}: {t.title}"
            if len(title) > 24:
                title = title[:21] + "..."

            # Bar construction
            # 1 unit = 4 chars: " [ ]" or "[==]"
            # Let's use 4 chars per unit
            indent = "    " * start

            status = str(t.status).lower()
            bar_char = "████"
            # ANSI Colors
            # Pending: Grey/White
            # In Progress: Blue
            # Completed: Green
            # Failed: Red

            color_code = "\033[0m" # Reset
            if status in ["completed", "done", "fixed", "resolved"]:
                color_code = "\033[92m" # Green
            elif status in ["in_progress", "active"]:
                color_code = "\033[94m" # Blue
            elif status in ["failed", "blocked"]:
                color_code = "\033[91m" # Red
            else:
                 color_code = "\033[90m" # Grey

            bar = f"{color_code}{bar_char}\033[0m"

            print(f"{title:<25} | {indent}{bar}")

def run_gantt_logic(project_dir: Path) -> bool:
    cli = GanttCLI(project_dir)
    if cli.load_tasks():
        cli.calculate_schedule()
        cli.render()
        return True
    return False
