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
    interval: Optional[int] = None  # seconds
    cron_expression: Optional[str] = None
    last_run: float = 0.0

    def get_next_run_time(self) -> float:
        """Calculates the next run timestamp."""
        if self.cron_expression:
            if self.last_run == 0.0:
                # If never run, run immediately (aligns with interval behavior)
                # Alternatively, we could wait for next cron slot:
                # return croniter(self.cron_expression, datetime.now()).get_next(float)
                # But immediate feedback is usually desired for "enabled" tasks.
                return 0.0

            # Use last_run as base.
            # Note: croniter expects a start time. get_next() returns the next occurrence *after* start time.
            try:
                c = croniter(self.cron_expression, datetime.fromtimestamp(self.last_run))
                return c.get_next(float)
            except Exception as e:
                print(f"Error calculating next run for {self.name}: {e}")
                return float('inf')

        elif self.interval is not None:
            if self.last_run == 0.0:
                return 0.0
            return self.last_run + self.interval
        else:
            return float('inf')

    def is_due(self) -> bool:
        return time.time() >= self.get_next_run_time()

    def time_until_due(self) -> float:
        next_run = self.get_next_run_time()
        if next_run == 0.0:
            return 0.0
        return max(0, next_run - time.time())

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

            self.tasks = []
            for item in data.get("tasks", []):
                try:
                    name = item.get("name", "Unnamed Task")
                    command = item.get("command")
                    interval_str = item.get("interval")
                    cron_expr = item.get("cron")

                    if not command:
                        print(f"Skipping invalid task '{name}': missing command")
                        continue

                    if not interval_str and not cron_expr:
                        print(f"Skipping invalid task '{name}': missing interval or cron")
                        continue

                    interval = None
                    if interval_str:
                        interval = parse_duration(str(interval_str))

                    # Initialize last_run to 0
                    self.tasks.append(Task(name, command, interval=interval, cron_expression=cron_expr))
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
                    "command": f"{sys.executable} main.py clean --force",
                    "cron": "0 0 * * 0" # Every Sunday at midnight
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

        print(f"{'Task':<30} | {'Schedule':<15} | {'Status':<20}")
        print("-" * 71)
        for task in self.tasks:
            # Schedule Display
            if task.cron_expression:
                schedule_display = f"Cron: {task.cron_expression}"
            elif task.interval:
                if task.interval >= 86400:
                    schedule_display = f"Int: {task.interval // 86400}d"
                elif task.interval >= 3600:
                    schedule_display = f"Int: {task.interval // 3600}h"
                elif task.interval >= 60:
                    schedule_display = f"Int: {task.interval // 60}m"
                else:
                    schedule_display = f"Int: {task.interval}s"
            else:
                schedule_display = "Invalid"

            # Status Display
            if task.last_run == 0:
                status = "Pending (Runs now)"
            else:
                next_run_ts = task.get_next_run_time()
                next_run = datetime.fromtimestamp(next_run_ts)
                status = f"Next: {next_run.strftime('%H:%M:%S')}"

            print(f"{task.name:<30} | {schedule_display:<15} | {status}")

    def start(self) -> None:
        if not self.tasks:
            print("No tasks loaded. Aborting start.")
            return

        print(f"Starting Scheduler with {len(self.tasks)} tasks...")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                # We need to sleep a bit, but also check regularly.
                # Calculating min_wait helps optimization.

                ran_any = False
                current_min_wait = float('inf')

                for task in self.tasks:
                    if task.is_due():
                        self.run_task(task)
                        ran_any = True

                    # Recalculate wait after potential run
                    wait = task.time_until_due()
                    if wait < current_min_wait:
                        current_min_wait = wait

                if current_min_wait == float('inf'):
                    current_min_wait = 60.0

                # Sleep but cap at 60s
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
