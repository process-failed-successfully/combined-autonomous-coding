import time
import subprocess
import shlex
import yaml
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from croniter import croniter

def parse_duration(duration_str: str) -> int:
    """Parses a duration string (e.g. '1h', '30m', '10s') into seconds."""
    duration_str = duration_str.lower().strip()
    if duration_str.endswith("s"):
        return int(duration_str[:-1])
    elif duration_str.endswith("m"):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith("h"):
        return int(duration_str[:-1]) * 3600
    elif duration_str.endswith("d"):
        return int(duration_str[:-1]) * 86400
    else:
        # Assume seconds if no suffix
        try:
            return int(duration_str)
        except ValueError:
            raise ValueError(f"Invalid duration format: {duration_str}")

@dataclass
class Task:
    name: str
    command: str
    interval: int = 0  # seconds
    cron_expression: Optional[str] = None
    last_run: float = 0.0

    def __post_init__(self):
        # If cron, init last_run to now so we calculate next run from now
        if self.cron_expression and self.last_run == 0:
            self.last_run = time.time()

    def is_due(self) -> bool:
        if self.cron_expression:
            now = time.time()
            # Check if next scheduled time after last_run has passed
            iter = croniter(self.cron_expression, datetime.fromtimestamp(self.last_run))
            next_run = iter.get_next(datetime).timestamp()
            return next_run <= now
        else:
            return time.time() - self.last_run >= self.interval

    def time_until_due(self) -> float:
        if self.cron_expression:
            if self.is_due():
                return 0.0

            # Calculate time to next run from NOW
            now = datetime.now()
            iter = croniter(self.cron_expression, now)
            next_run = iter.get_next(datetime)
            return (next_run - now).total_seconds()
        else:
            return max(0, self.interval - (time.time() - self.last_run))

class Scheduler:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.config_path = self.project_dir / "scheduler.yaml"
        self.tasks: List[Task] = []

    def load_config(self) -> None:
        if not self.config_path.exists():
            print(f"No scheduler config found at {self.config_path}.")
            print("Run 'main.py scheduler init' to create one.")
            return

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f) or {}

            for item in data.get("tasks", []):
                try:
                    name = item.get("name", "Unnamed Task")
                    command = item.get("command")
                    interval_str = item.get("interval")

                    if not command or not interval_str:
                        print(f"Skipping invalid task '{name}': missing command or interval")
                        continue

                    cron_expr = None
                    interval = 0

                    # Check if cron expression (contains spaces)
                    if " " in str(interval_str).strip():
                        if croniter.is_valid(str(interval_str)):
                            cron_expr = str(interval_str)
                        else:
                            print(f"Invalid cron expression for task '{name}': {interval_str}")
                            continue
                    else:
                        interval = parse_duration(str(interval_str))

                    self.tasks.append(Task(name, command, interval, cron_expr))
                except ValueError as e:
                    print(f"Error parsing task '{item.get('name')}': {e}")

        except Exception as e:
            print(f"Error loading scheduler config: {e}")

    def init_config(self) -> bool:
        if self.config_path.exists():
            return False

        default_config = {
            "tasks": [
                {
                    "name": "Hourly Health Check",
                    "command": f"{sys.executable} main.py health",
                    "interval": "1h"
                },
                {
                    "name": "Daily Dependency Check",
                    "command": f"{sys.executable} main.py deps --check",
                    "interval": "24h"
                },
                {
                    "name": "Weekly Cleanup (Cron Example)",
                    "command": f"{sys.executable} main.py clean --archive",
                    "interval": "0 0 * * 0" # Every Sunday at midnight
                }
            ]
        }

        try:
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, sort_keys=False, indent=2)
            return True
        except Exception as e:
            print(f"Error creating config: {e}")
            return False

    def list_tasks(self) -> None:
        if not self.tasks:
            print("No tasks scheduled.")
            return

        print(f"{'Task':<30} | {'Interval/Cron':<20} | {'Status':<20}")
        print("-" * 76)
        for task in self.tasks:
            if task.cron_expression:
                interval_display = task.cron_expression
                iter = croniter(task.cron_expression, datetime.now())
                next_run = iter.get_next(datetime)
                status = f"Next: {next_run.strftime('%H:%M:%S')}"
            else:
                if task.last_run == 0:
                    status = "Pending (Runs now)"
                else:
                    next_run = datetime.fromtimestamp(task.last_run) + timedelta(seconds=task.interval)
                    status = f"Next: {next_run.strftime('%H:%M:%S')}"

                interval_display = f"{task.interval}s"
                if task.interval >= 86400:
                    interval_display = f"{task.interval // 86400}d"
                elif task.interval >= 3600:
                    interval_display = f"{task.interval // 3600}h"
                elif task.interval >= 60:
                    interval_display = f"{task.interval // 60}m"

            print(f"{task.name:<30} | {interval_display:<20} | {status}")

    def start(self) -> None:
        if not self.tasks:
            print("No tasks loaded. Aborting start.")
            return

        print(f"Starting Scheduler with {len(self.tasks)} tasks...")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                now = time.time()
                min_wait = 60.0 # Default wait time

                for task in self.tasks:
                    if task.is_due():
                        self.run_task(task)
                        # Recheck if others are due? No, proceed.

                    wait = task.time_until_due()
                    if wait < min_wait:
                        min_wait = wait

                # Re-calculate min_wait after runs
                current_min_wait = float('inf')
                for task in self.tasks:
                    wait = task.time_until_due()
                    if wait < current_min_wait:
                        current_min_wait = wait

                if current_min_wait == float('inf'):
                    current_min_wait = 60.0

                # Sleep but cap at 60s to allow for interrupts/updates
                sleep_time = min(max(1.0, current_min_wait), 60.0)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nScheduler stopped.")

    def run_task(self, task: Task) -> None:
        print(f"\n[Scheduler] Running: {task.name}")
        task.last_run = time.time()

        try:
            cmd_parts = shlex.split(task.command)

            result = subprocess.run(
                cmd_parts,
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ {task.name} completed.")
                if result.stdout:
                    # Print summary (first line)
                    print(f"   Output: {result.stdout.strip().splitlines()[0]}...")
            else:
                print(f"❌ {task.name} failed (exit code {result.returncode}).")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")

        except Exception as e:
            print(f"❌ Error executing {task.name}: {e}")
